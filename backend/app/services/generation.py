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
    MemberSpotlightBlock,
    NewsletterOutput,
    SocialPostOutput,
    TipsCtaBlock,
)
from app.services.prompts import (
    build_boilerplate_prompt,
    build_events_list_prompt,
    build_feature_article_prompt,
    build_grant_flyer_prompt,
    build_member_spotlight_prompt,
    build_tips_cta_prompt,
    get_all_prompts,
    resolve_variant,
)


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
    
    return {
        "name": tool_name,
        "description": description,
        "input_schema": {
            "type": "object",
            "properties": json_schema.get("properties", {}),
            "required": json_schema.get("required", []),
        },
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
        model="claude-sonnet-4-20250514",
        max_tokens=2048,
        tools=[tool],
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
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        tools=[tool],
        messages=[{"role": "user", "content": prompt}],
    )
    
    tool_use_block = next((block for block in response.content if block.type == "tool_use"), None)
    if not tool_use_block:
        raise ValueError("Claude did not return a tool use block")
    
    return HashtagsOutput(**tool_use_block.input)


async def generate_newsletter(client: anthropic.Anthropic, prompt: str) -> NewsletterOutput:
    """Generate newsletter/email content using Claude with structured output."""
    tool = pydantic_to_anthropic_tool(
        NewsletterOutput,
        "create_newsletter",
        "Create newsletter content with subject line, preview text, body HTML, and CTA"
    )
    
    response = await asyncio.to_thread(
        client.messages.create,
        model="claude-sonnet-4-20250514",
        max_tokens=2048,
        tools=[tool],
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
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        tools=[tool],
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
        model="claude-sonnet-4-20250514",
        max_tokens=4096,
        tools=[tool],
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
        model="claude-sonnet-4-20250514",
        max_tokens=2048,
        tools=[tool],
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
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        tools=[tool],
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
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        tools=[tool],
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
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        tools=[tool],
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
        model="claude-sonnet-4-20250514",
        max_tokens=1536,
        tools=[tool],
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
        model="claude-sonnet-4-20250514",
        max_tokens=512,
        tools=[tool],
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
    social_post_variant_selection: str = "generate_new",
    newsletter_variant_selection: str = "generate_new",
    recent_social_post_variants: list[str] | None = None,
    recent_newsletter_variants: list[str] | None = None,
    keymakers_stage_key: str | None = None,
) -> tuple[GeneratedContentResponse, str, str]:
    """
    Generate all content types concurrently.
    This is the main entry point for content generation.

    social_post_variant_selection / newsletter_variant_selection accept the
    same values as the frontend dropdown: "generate_new", "avoid_recent", or
    an explicit variant key (see app/services/prompts.resolve_variant).
    `recent_*_variants` should be recent structure_variant history for this
    event/content type when selection is "avoid_recent" — pass None until
    the database is wired up (falls back to "generate_new" behavior).

    keymakers_stage_key, when set, switches the newsletter into Keymakers
    recruitment-copy mode (see prompts.build_newsletter_prompt /
    keymakers_campaign.py) — newsletter_variant_selection is ignored in
    that case, since the reference message supplies its own structure.
    Only the newsletter is affected.

    Returns the generated content plus the two resolved variant keys, so
    callers can persist which variant was actually used. When
    keymakers_stage_key is set, the returned newsletter_variant is that
    stage key (so the caller can persist which Keymakers stage was used,
    the same way structure_variant is persisted for the non-Keymakers path).
    """
    client = get_anthropic_client()

    social_post_variant = resolve_variant(
        "social_post", social_post_variant_selection, recent_social_post_variants
    )
    newsletter_variant = (
        keymakers_stage_key
        if keymakers_stage_key
        else resolve_variant("newsletter", newsletter_variant_selection, recent_newsletter_variants)
    )

    prompts = get_all_prompts(
        event,
        social_post_variant=social_post_variant,
        newsletter_variant=newsletter_variant,
        keymakers_stage_key=keymakers_stage_key,
    )

    # Run all generations concurrently
    social_post, hashtags, newsletter, flyer, calendar = await asyncio.gather(
        generate_social_post(client, prompts["social_post"]),
        generate_hashtags(client, prompts["hashtags"]),
        generate_newsletter(client, prompts["newsletter"]),
        generate_flyer(client, prompts["flyer"]),
        generate_calendar(client, prompts["calendar"]),
    )

    result = GeneratedContentResponse(
        social_post=social_post,
        hashtags=hashtags,
        newsletter=newsletter,
        flyer=flyer,
        calendar=calendar,
    )
    return result, social_post_variant, newsletter_variant
