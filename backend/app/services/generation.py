"""
Core generation logic using Claude API with structured outputs (tool use).
Calls all three content generators concurrently via asyncio.gather.
"""

import asyncio
import json
import os
from typing import Any

import anthropic
from anthropic.types import MessageParam

from app.schemas import (
    BoilerplateBlock,
    ContentCalendarOutput,
    EventInput,
    EventsListBlock,
    FeatureArticleBlock,
    FlyerOutput,
    GeneratedContentResponse,
    GrantFlyerBlock,
    HashtagsOutput,
    HashtagsVariant,
    MemberSpotlightBlock,
    NewsletterOutput,
    SocialPostOutput,
    SocialPostVariant,
    TipsCtaBlock,
)
from app.services.prompts import (
    SOCIAL_POST_ANGLE_HINTS,
    SOCIAL_POST_VARIANTS,
    build_boilerplate_prompt,
    build_calendar_prompt,
    build_events_list_prompt,
    build_feature_article_prompt,
    build_flyer_prompt,
    build_grant_flyer_prompt,
    build_hashtags_prompt,
    build_member_spotlight_prompt,
    build_newsletter_prompt,
    build_social_post_prompt,
    build_tips_cta_prompt,
    resolve_variant,
)

# How many social post / hashtag options staff compares on the review page
# before picking one — see GeneratedContentResponse.social_post_variants.
SOCIAL_POST_VARIANT_COUNT = 3

# The 3 tone variants used for a batch when no platform was explicitly
# selected — deliberately the non-platform keys from SOCIAL_POST_VARIANTS,
# since those are 3 genuinely distinct shapes (not 3 near-identical
# rewrites). Kept as its own tuple rather than reusing
# RANDOM_POOL_EXCLUDED's complement so this list is explicit and stable
# even if the variant registry grows later.
DEFAULT_BATCH_TONE_VARIANTS: tuple[str, ...] = ("standard", "listicle", "quote_style")


def get_anthropic_client() -> anthropic.Anthropic:
    """Initialize Anthropic client with API key from environment."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY environment variable not set")
    return anthropic.Anthropic(api_key=api_key)


def pydantic_to_anthropic_tool(schema_class, tool_name: str, description: str) -> dict[str, Any]:
    """
    Convert a Pydantic model to Anthropic tool schema format.
    This forces Claude to return structured JSON matching our schemas.
    """
    json_schema = schema_class.model_json_schema()

    input_schema: dict[str, Any] = {
        "type": "object",
        "properties": json_schema.get("properties", {}),
        "required": json_schema.get("required", []),
    }
    # Nested models (e.g. ContentCalendarOutput.entries: list[CalendarPostEntry])
    # get hoisted by Pydantic into a top-level $defs block, with $ref pointers
    # left in their place — without forwarding $defs, those refs point at
    # nothing and Claude has to guess the nested shape (previously observed:
    # calendar entries missing hashtags/platform/post_idea entirely).
    if "$defs" in json_schema:
        input_schema["$defs"] = json_schema["$defs"]

    return {
        "name": tool_name,
        "description": description,
        "input_schema": input_schema,
    }


async def generate_social_post(client: anthropic.Anthropic, prompt: str) -> SocialPostOutput:
    """Generate social media post using Claude with structured output."""
    tool = pydantic_to_anthropic_tool(
        SocialPostOutput,
        "create_social_post",
        "Create a WVF-branded social media post with caption, hashtags, image prompt, and CTA"
    )

    # Use asyncio.to_thread to run sync API call in executor
    response = await asyncio.to_thread(
        client.messages.create,
        model="claude-sonnet-5",
        max_tokens=2048,
        tools=[tool],
        tool_choice={"type": "tool", "name": tool["name"]},
        messages=[{"role": "user", "content": prompt}],
    )

    # Extract tool use from response
    tool_use_block = next((block for block in response.content if block.type == "tool_use"), None)
    if not tool_use_block:
        raise ValueError("Claude did not return a tool use block")

    return SocialPostOutput(**tool_use_block.input)


async def generate_hashtags(client: anthropic.Anthropic, prompt: str) -> HashtagsOutput:
    """Generate hashtag recommendations using Claude with structured output."""
    tool = pydantic_to_anthropic_tool(
        HashtagsOutput,
        "recommend_hashtags",
        "Recommend primary brand hashtags and topic-specific hashtags for the event"
    )

    response = await asyncio.to_thread(
        client.messages.create,
        model="claude-sonnet-5",
        max_tokens=1024,
        tools=[tool],
        tool_choice={"type": "tool", "name": tool["name"]},
        messages=[{"role": "user", "content": prompt}],
    )

    tool_use_block = next((block for block in response.content if block.type == "tool_use"), None)
    if not tool_use_block:
        raise ValueError("Claude did not return a tool use block")

    return HashtagsOutput(**tool_use_block.input)


def _resolve_batch_variants(social_post_platform: str | None) -> list[tuple[str, str | None]]:
    """
    Returns SOCIAL_POST_VARIANT_COUNT (structure_variant, angle_hint) pairs
    for one generation batch.

    - No platform selected: use the 3 fixed tone variants
      (DEFAULT_BATCH_TONE_VARIANTS) — each is already a genuinely distinct
      shape, so no angle_hint is needed.
    - Platform explicitly selected: keep that platform's structure fixed
      across all 3 (staff deliberately chose it), and instead vary the
      opening angle via SOCIAL_POST_ANGLE_HINTS so the 3 results are
      different posts, not near-identical rewrites of the same hook.
    """
    if social_post_platform:
        return [
            (social_post_platform, angle)
            for angle in SOCIAL_POST_ANGLE_HINTS[:SOCIAL_POST_VARIANT_COUNT]
        ]
    return [(variant, None) for variant in DEFAULT_BATCH_TONE_VARIANTS[:SOCIAL_POST_VARIANT_COUNT]]


async def generate_social_post_variants(
    client: anthropic.Anthropic,
    event: EventInput,
    social_post_platform: str | None = None,
    series: str | None = None,
    tone: str | None = None,
) -> list[SocialPostVariant]:
    """
    Generate SOCIAL_POST_VARIANT_COUNT distinct social post options
    concurrently, for staff to compare and pick from on the review page —
    see GeneratedContentResponse.social_post_variants. See
    _resolve_batch_variants for how the 3 are differentiated.

    series / tone: optional staff steering, applied identically across all
    3 options in the batch (see build_social_post_prompt / prompts.py's
    SOCIAL_POST_SERIES_HINTS and SOCIAL_POST_TONE_HINTS).
    """
    batch = _resolve_batch_variants(social_post_platform)

    async def run_one(structure_variant: str, angle_hint: str | None) -> SocialPostVariant:
        prompt = build_social_post_prompt(
            event, structure_variant, angle_hint=angle_hint, series=series, tone=tone
        )
        post = await generate_social_post(client, prompt)
        return SocialPostVariant(
            structure_variant=structure_variant,
            structure_label=SOCIAL_POST_VARIANTS[structure_variant]["label"],
            post=post,
        )

    return list(await asyncio.gather(*(run_one(sv, angle) for sv, angle in batch)))


async def generate_hashtags_variants(
    client: anthropic.Anthropic, event: EventInput, count: int = SOCIAL_POST_VARIANT_COUNT
) -> list[HashtagsVariant]:
    """
    Generate `count` hashtag-set options concurrently, paired 1:1 by index
    with generate_social_post_variants()'s output on the review page. Each
    call uses the same hashtags prompt (hashtags aren't keyed to a
    structure_variant) — Claude's own sampling gives 3 distinct-enough
    real sets without needing an artificial angle hint.
    """
    prompt = build_hashtags_prompt(event)

    async def run_one() -> HashtagsVariant:
        return HashtagsVariant(hashtags=await generate_hashtags(client, prompt))

    return list(await asyncio.gather(*(run_one() for _ in range(count))))


async def generate_newsletter(client: anthropic.Anthropic, prompt: str) -> NewsletterOutput:
    """Generate newsletter/email content using Claude with structured output."""
    tool = pydantic_to_anthropic_tool(
        NewsletterOutput,
        "create_newsletter",
        "Create newsletter content with subject line, preview text, body HTML, and CTA"
    )
    
    response = await asyncio.to_thread(
        client.messages.create,
        model="claude-sonnet-5",
        max_tokens=2048,
        tools=[tool],
        tool_choice={"type": "tool", "name": tool["name"]},
        messages=[{"role": "user", "content": prompt}],
    )

    tool_use_block = next((block for block in response.content if block.type == "tool_use"), None)
    if not tool_use_block:
        raise ValueError("Claude did not return a tool use block")

    return NewsletterOutput(**tool_use_block.input)


async def generate_flyer(client: anthropic.Anthropic, prompt: str) -> FlyerOutput:
    """Generate event flyer copy using Claude with structured output."""
    tool = pydantic_to_anthropic_tool(
        FlyerOutput,
        "create_flyer_copy",
        "Create WVF-branded flyer copy with headline, subheadline, body, CTA, and footer details"
    )

    response = await asyncio.to_thread(
        client.messages.create,
        model="claude-sonnet-5",
        max_tokens=1024,
        tools=[tool],
        tool_choice={"type": "tool", "name": tool["name"]},
        messages=[{"role": "user", "content": prompt}],
    )

    tool_use_block = next((block for block in response.content if block.type == "tool_use"), None)
    if not tool_use_block:
        raise ValueError("Claude did not return a tool use block")

    return FlyerOutput(**tool_use_block.input)


async def generate_calendar(client: anthropic.Anthropic, prompt: str) -> ContentCalendarOutput:
    """Generate a multi-week content calendar using Claude with structured output."""
    tool = pydantic_to_anthropic_tool(
        ContentCalendarOutput,
        "create_content_calendar",
        "Create a multi-week content calendar with platform-varied post entries, hashtags, and CTAs"
    )

    response = await asyncio.to_thread(
        client.messages.create,
        model="claude-sonnet-5",
        max_tokens=4096,
        tools=[tool],
        tool_choice={"type": "tool", "name": tool["name"]},
        messages=[{"role": "user", "content": prompt}],
    )

    tool_use_block = next((block for block in response.content if block.type == "tool_use"), None)
    if not tool_use_block:
        raise ValueError("Claude did not return a tool use block")

    return ContentCalendarOutput(**tool_use_block.input)


async def generate_feature_article(client: anthropic.Anthropic, prompt: str) -> FeatureArticleBlock:
    """Generate the feature_article newsletter block."""
    tool = pydantic_to_anthropic_tool(
        FeatureArticleBlock,
        "create_feature_article",
        "Create a long-form educational newsletter feature article",
    )
    response = await asyncio.to_thread(
        client.messages.create,
        model="claude-sonnet-5",
        max_tokens=2048,
        tools=[tool],
        tool_choice={"type": "tool", "name": tool["name"]},
        messages=[{"role": "user", "content": prompt}],
    )
    tool_use_block = next((block for block in response.content if block.type == "tool_use"), None)
    if not tool_use_block:
        raise ValueError("Claude did not return a tool use block")
    return FeatureArticleBlock(**tool_use_block.input)


async def generate_events_list(client: anthropic.Anthropic, prompt: str) -> EventsListBlock:
    """Generate the events_list newsletter block."""
    tool = pydantic_to_anthropic_tool(
        EventsListBlock,
        "create_events_list",
        "Create an upcoming-events list entry for the newsletter",
    )
    response = await asyncio.to_thread(
        client.messages.create,
        model="claude-sonnet-5",
        max_tokens=1024,
        tools=[tool],
        tool_choice={"type": "tool", "name": tool["name"]},
        messages=[{"role": "user", "content": prompt}],
    )
    tool_use_block = next((block for block in response.content if block.type == "tool_use"), None)
    if not tool_use_block:
        raise ValueError("Claude did not return a tool use block")
    return EventsListBlock(**tool_use_block.input)


async def generate_grant_flyer(client: anthropic.Anthropic, prompt: str) -> GrantFlyerBlock:
    """Generate the grant_flyer newsletter block."""
    tool = pydantic_to_anthropic_tool(
        GrantFlyerBlock,
        "create_grant_flyer",
        "Create a grant/funding opportunity entry for the newsletter",
    )
    response = await asyncio.to_thread(
        client.messages.create,
        model="claude-sonnet-5",
        max_tokens=1024,
        tools=[tool],
        tool_choice={"type": "tool", "name": tool["name"]},
        messages=[{"role": "user", "content": prompt}],
    )
    tool_use_block = next((block for block in response.content if block.type == "tool_use"), None)
    if not tool_use_block:
        raise ValueError("Claude did not return a tool use block")
    return GrantFlyerBlock(**tool_use_block.input)


async def generate_tips_cta(client: anthropic.Anthropic, prompt: str) -> TipsCtaBlock:
    """Generate the tips_cta newsletter block."""
    tool = pydantic_to_anthropic_tool(
        TipsCtaBlock,
        "create_tips_cta",
        "Create a short promotional tips/CTA block for the newsletter",
    )
    response = await asyncio.to_thread(
        client.messages.create,
        model="claude-sonnet-5",
        max_tokens=1024,
        tools=[tool],
        tool_choice={"type": "tool", "name": tool["name"]},
        messages=[{"role": "user", "content": prompt}],
    )
    tool_use_block = next((block for block in response.content if block.type == "tool_use"), None)
    if not tool_use_block:
        raise ValueError("Claude did not return a tool use block")
    return TipsCtaBlock(**tool_use_block.input)


async def generate_member_spotlight(client: anthropic.Anthropic, prompt: str) -> MemberSpotlightBlock:
    """Generate the member_spotlight newsletter block."""
    tool = pydantic_to_anthropic_tool(
        MemberSpotlightBlock,
        "create_member_spotlight",
        "Create a Key Maker/member spotlight testimonial block for the newsletter",
    )
    response = await asyncio.to_thread(
        client.messages.create,
        model="claude-sonnet-5",
        max_tokens=1536,
        tools=[tool],
        tool_choice={"type": "tool", "name": tool["name"]},
        messages=[{"role": "user", "content": prompt}],
    )
    tool_use_block = next((block for block in response.content if block.type == "tool_use"), None)
    if not tool_use_block:
        raise ValueError("Claude did not return a tool use block")
    return MemberSpotlightBlock(**tool_use_block.input)


async def generate_boilerplate(client: anthropic.Anthropic, prompt: str) -> BoilerplateBlock:
    """Generate the boilerplate newsletter block."""
    tool = pydantic_to_anthropic_tool(
        BoilerplateBlock,
        "create_boilerplate",
        "Create the static About WVF + footer boilerplate block",
    )
    response = await asyncio.to_thread(
        client.messages.create,
        model="claude-sonnet-5",
        max_tokens=512,
        tools=[tool],
        tool_choice={"type": "tool", "name": tool["name"]},
        messages=[{"role": "user", "content": prompt}],
    )
    tool_use_block = next((block for block in response.content if block.type == "tool_use"), None)
    if not tool_use_block:
        raise ValueError("Claude did not return a tool use block")
    return BoilerplateBlock(**tool_use_block.input)


# block_type -> (prompt builder, generator function). Used by
# generate_newsletter_blocks() to dispatch each requested block type.
NEWSLETTER_BLOCK_GENERATORS = {
    "feature_article": (build_feature_article_prompt, generate_feature_article),
    "events_list": (build_events_list_prompt, generate_events_list),
    "grant_flyer": (build_grant_flyer_prompt, generate_grant_flyer),
    "tips_cta": (build_tips_cta_prompt, generate_tips_cta),
    "member_spotlight": (build_member_spotlight_prompt, generate_member_spotlight),
    "boilerplate": (build_boilerplate_prompt, generate_boilerplate),
}


async def generate_newsletter_blocks(
    event: EventInput,
    block_types: list[str],
    key_maker_business_name: str | None = None,
    key_maker_owner_name: str | None = None,
    key_maker_business_type: str | None = None,
) -> dict[str, Any]:
    """
    Generate the requested newsletter blocks concurrently.

    `block_types` should be a subset of NEWSLETTER_BLOCK_GENERATORS keys
    (see app/models/content.py NewsletterBlockType) — callers can request
    any combination, since the PRD says blocks may be swapped/dropped/
    reordered per issue rather than always generating all six.

    `key_maker_*` fields are only used when 'member_spotlight' is
    requested; pass real KeyMaker row data when available (see
    app/routers/newsletter_blocks.py) or omit for a placeholder spotlight.

    Returns {block_type: <block output model instance>}.
    """
    unknown = set(block_types) - set(NEWSLETTER_BLOCK_GENERATORS.keys())
    if unknown:
        raise ValueError(
            f"Unknown newsletter block type(s): {unknown}. "
            f"Valid options: {list(NEWSLETTER_BLOCK_GENERATORS.keys())}"
        )

    client = get_anthropic_client()

    async def run_one(block_type: str):
        prompt_builder, generator = NEWSLETTER_BLOCK_GENERATORS[block_type]
        if block_type == "member_spotlight":
            prompt = prompt_builder(
                event,
                key_maker_business_name=key_maker_business_name,
                key_maker_owner_name=key_maker_owner_name,
                key_maker_business_type=key_maker_business_type,
            )
        elif block_type == "boilerplate":
            prompt = prompt_builder()
        else:
            prompt = prompt_builder(event)
        return block_type, await generator(client, prompt)

    results = await asyncio.gather(*(run_one(bt) for bt in block_types))
    return dict(results)


async def generate_all_content(
    event: EventInput,
    social_post_platform: str | None = None,
    newsletter_variant_selection: str = "generate_new",
    recent_newsletter_variants: list[str] | None = None,
    keymakers_stage_key: str | None = None,
    social_post_series: str | None = None,
    social_post_tone: str | None = None,
) -> tuple[GeneratedContentResponse, str]:
    """
    Generate all content types concurrently.
    This is the main entry point for content generation.

    social_post_platform: when set (instagram/linkedin/facebook/x/tiktok —
    an explicit staff choice, not random), all SOCIAL_POST_VARIANT_COUNT
    social post options in the batch stay on that platform, varying only
    the opening angle (see generate_social_post_variants). When None, the
    batch uses the 3 fixed tone variants instead. Social posts and
    hashtags are no longer single-generation/single-persisted — see
    GeneratedContentResponse.social_post_variants /
    .hashtags_variants and POST /api/content/select-social-variant for
    the pick-then-persist flow.

    newsletter_variant_selection accepts the same values as the frontend
    dropdown: "generate_new", "avoid_recent", or an explicit variant key
    (see app/services/prompts.resolve_variant). `recent_newsletter_variants`
    should be recent structure_variant history for the newsletter content
    type when selection is "avoid_recent" — pass None until the database is
    wired up (falls back to "generate_new" behavior).

    keymakers_stage_key, when set, switches the newsletter into Keymakers
    recruitment-copy mode (see prompts.build_newsletter_prompt /
    keymakers_campaign.py) — newsletter_variant_selection is ignored in
    that case, since the reference message supplies its own structure.
    Only the newsletter is affected.

    social_post_series / social_post_tone: optional staff steering for the
    social post batch only (see prompts.py's SOCIAL_POST_SERIES_HINTS /
    SOCIAL_POST_TONE_HINTS) — applied identically across all 3 options in
    the batch. Unknown/unset values are silently ignored.

    Returns the generated content plus the resolved newsletter variant key,
    so the caller can persist which variant was actually used (newsletter
    is still generated/persisted as a single item, unlike social_post).
    When keymakers_stage_key is set, the returned value is that stage key.
    """
    client = get_anthropic_client()

    newsletter_variant = (
        keymakers_stage_key
        if keymakers_stage_key
        else resolve_variant("newsletter", newsletter_variant_selection, recent_newsletter_variants)
    )

    newsletter_prompt = build_newsletter_prompt(
        event, newsletter_variant, keymakers_stage_key=keymakers_stage_key
    )
    flyer_prompt = build_flyer_prompt(event)
    calendar_prompt = build_calendar_prompt(event)

    # Run all generations concurrently, including both social-post-variant
    # and hashtags-variant batches (each of those is itself
    # SOCIAL_POST_VARIANT_COUNT concurrent calls internally).
    social_post_variants, hashtags_variants, newsletter, flyer, calendar = await asyncio.gather(
        generate_social_post_variants(
            client, event, social_post_platform, series=social_post_series, tone=social_post_tone
        ),
        generate_hashtags_variants(client, event),
        generate_newsletter(client, newsletter_prompt),
        generate_flyer(client, flyer_prompt),
        generate_calendar(client, calendar_prompt),
    )

    result = GeneratedContentResponse(
        social_post_variants=social_post_variants,
        hashtags_variants=hashtags_variants,
        newsletter=newsletter,
        flyer=flyer,
        calendar=calendar,
    )
    return result, newsletter_variant
