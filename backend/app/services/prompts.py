"""
Prompt templates for each content type.
Each function takes EventInput and returns a formatted prompt string.

Structure variants: per docs/PROJECT_CONTEXT.md, WVF wants content structure
to rotate rather than repeat the same shape every time (to keep engaging
shifting social algorithms). Each content type below defines a small set of
named variants in its own `*_VARIANTS` dict — each maps a variant key to a
label (for a future UI dropdown) and a block of structural instructions
spliced into the base prompt. See `resolve_variant()` for selection modes.
"""

import random

from app.schemas import EventInput
from app.services.brand_voice import get_brand_voice_context


SOCIAL_POST_VARIANTS: dict[str, dict[str, str]] = {
    "standard": {
        "label": "Standard",
        "instructions": """- Keep caption under 150 words (2-3 short paragraphs)
- Lead with the benefit/hook (why should they care?)
- Include key details (date, time, what they'll learn)
- End with a clear CTA ("Register Now", "Save Your Spot", etc.)""",
    },
    "listicle": {
        "label": "Listicle",
        "instructions": """- Structure the caption as a short numbered or bulleted list (e.g. "3 things you'll walk away with")
- Keep each list item to one line
- Open with a one-line hook before the list, close with a clear CTA
- Keep total caption under 150 words""",
    },
    "quote_style": {
        "label": "Quote-style",
        "instructions": """- Open with a short, punchy quote-style line in quotation marks (a compelling one-liner about the event's core benefit)
- Follow with 1-2 sentences of context and event details
- End with a clear CTA
- Keep total caption under 150 words""",
    },
    # --- Per-platform variants below ---
    # Grounded in real WVF Facebook/Instagram/LinkedIn post screenshots
    # (provided August 2026), not generic assumptions. Each platform has an
    # observably distinct real pattern — see docs/CONTENT_SCOPE.md for the
    # sourcing note. These override the generic "emojis sparingly" guidance
    # in build_social_post_prompt() where the real platform pattern
    # actually uses emoji heavily (Facebook).
    "instagram": {
        "label": "Instagram",
        "instructions": """- Short, punchy caption — 2-4 short lines, not paragraphs
- Lead with a bold, short hook (title-case or caps style, e.g. "MONEY & CREDIT", "ARE YOU READY?")
- 1-2 sentences of context max — Instagram captions get skimmed, not read
- End with a clear, brief CTA ("Register Now", "Save Your Spot")
- Keep total caption under 80 words — shorter than other platforms""",
    },
    "linkedin": {
        "label": "LinkedIn",
        "instructions": """- Professional framing — address the reader as a business owner/entrepreneur, not a general audience
- Open with a direct statement of the business problem or opportunity (e.g. "Small businesses are the #1 target for cyberattacks")
- 1-2 short paragraphs of context — can be slightly more detailed/credential-forward than Instagram (mention speaker expertise, program track record)
- Include concrete takeaways as a short list where relevant
- End with a clear CTA and a professional sign-off tone
- Keep total caption under 130 words""",
    },
    "facebook": {
        "label": "Facebook",
        "instructions": """- Open with an emoji-led hook line (e.g. "🚨WVF is FUNDING🚨", "Ready to become LOAN READY?")
- Follow with 1-2 sentences of context/invitation
- Structure key takeaways as a checklist using ✔ before each line (this is WVF's real observed Facebook pattern — do NOT use plain bullets here)
- Include logistics as labeled lines with emoji markers: 📅 for date, 🕐 for time, 📍 for location, 💻 for virtual/Zoom
- If applicable, add urgency framing (e.g. "⚠️ONLY 10 SPACES REMAINING", "Apply today before registration closes")
- End with 🔗 Register Now: [link] style CTA
- This is the one platform where heavier emoji use matches WVF's real voice — do not sparingly use emojis here
- Total caption can run longer than Instagram/LinkedIn — up to 180 words, matching WVF's real Facebook post length""",
    },
    # --- X and TikTok below ---
    # UNLIKE instagram/linkedin/facebook above, these are NOT grounded in
    # real observed WVF posts on these platforms — no WVF X or TikTok
    # samples have been reviewed yet. These are general platform
    # conventions only. Do not describe this as "WVF's real X/TikTok
    # style" anywhere (prompt copy or frontend UI) until real samples are
    # provided and this comment is updated — see instagram/linkedin/
    # facebook above for what that grounding looks like once available.
    "x": {
        "label": "X",
        "instructions": """- Short and punchy — X rewards brevity; keep the full caption well under 280 characters
- Lead with the single most compelling fact or hook, no preamble
- 1 short sentence of context at most
- End with a brief, direct CTA
- General platform convention, not yet grounded in reviewed WVF X posts""",
    },
    "tiktok": {
        "label": "TikTok",
        "instructions": """- Written as a caption accompanying a short video, not a standalone post — assume a video carries the main message
- Open with a hook line written for a scroll-stopping moment, casual tone
- Keep it short — a line or two, not a paragraph
- End with a brief CTA
- General platform convention, not yet grounded in reviewed WVF TikTok posts""",
    },
}

# Platform-keyed variants specifically — for a frontend "which platform"
# selector, distinct from the tone-keyed variants (standard/listicle/
# quote_style) which apply within any platform. instagram/linkedin/
# facebook are grounded in real WVF post screenshots; x/tiktok are
# generic conventions only — see the comment above the "x" entry in
# SOCIAL_POST_VARIANTS.
SOCIAL_POST_PLATFORM_VARIANTS = ("instagram", "linkedin", "facebook", "x", "tiktok")


# Used only when generating a 3-variant batch on a single, explicitly
# selected platform (see generate_social_post_variants in generation.py) —
# the platform's structural rules (SOCIAL_POST_VARIANTS[platform]) stay
# fixed across all 3, but each gets a different opening-angle instruction
# layered on top so the 3 results are genuinely different posts, not 3
# near-identical rewrites of the same hook.
SOCIAL_POST_ANGLE_HINTS: tuple[str, ...] = (
    "Lead with the concrete benefit/outcome an attendee walks away with.",
    "Lead with the problem or pain point this event solves for the reader.",
    "Lead with urgency or social proof (e.g. limited spots, who else is attending/hosting).",
)


def build_social_post_prompt(
    event: EventInput, variant: str = "standard", angle_hint: str | None = None
) -> str:
    """
    Build prompt for social media post generation.
    Target: under 150 words, includes CTA, uses brand hashtags.

    `variant` selects a structural shape from SOCIAL_POST_VARIANTS — either
    a tone variant (standard/listicle/quote_style) or a platform variant
    (instagram/linkedin/facebook, see SOCIAL_POST_PLATFORM_VARIANTS). See
    resolve_variant() for how callers should choose one (generate new /
    avoid recent repeats / explicit pick).

    `angle_hint`, when set, adds one extra instruction on top of `variant`'s
    fixed structure — used to differentiate posts within a 3-variant batch
    that's pinned to one platform (see SOCIAL_POST_ANGLE_HINTS above).
    """
    brand_context = get_brand_voice_context()
    structure = SOCIAL_POST_VARIANTS[variant]["instructions"]
    is_platform_variant = variant in SOCIAL_POST_PLATFORM_VARIANTS

    # Tone variants (standard/listicle/quote_style) have no platform
    # context to draw emoji density from, so they default to sparing use.
    # Platform variants specify their own real, observed emoji usage
    # directly in `structure` above (see SOCIAL_POST_VARIANTS) — the
    # shared brand_voice.py guidance no longer contradicts this (fixed to
    # say "match platform-specific density", not a blanket "sparingly").
    emoji_guidance = (
        "" if is_platform_variant else "\n- Use emojis sparingly (🚨 for urgency, 📅 for dates, ✅ for benefits)"
    )
    angle_instruction = f"\n- {angle_hint}" if angle_hint else ""

    return f"""You are a social media content creator for Women's Venture Fund (WVF), a NYC-based CDFI supporting women entrepreneurs.

{brand_context}

Your task: Create a social media post for this event:

**Event Details:**
- Title: {event.title}
- Date: {event.date}
- Speaker: {event.speaker}
- Registration: {event.registration_link}
- Target Audience: {event.audience}
- Description: {event.description}

**Requirements:**
{structure}
- Suggest 5-7 hashtags from the brand list + topic-specific ones
- Write a DALL-E style image prompt (describe a professional, engaging visual)
- Match the tone from the examples: direct, benefit-forward, warm but professional{emoji_guidance}{angle_instruction}

Return structured JSON matching the SocialPostOutput schema."""


def build_hashtags_prompt(event: EventInput) -> str:
    """
    Build prompt for standalone hashtag recommendations.
    Separates brand hashtags from topic-specific ones.
    """
    brand_context = get_brand_voice_context()
    
    return f"""You are a social media strategist for Women's Venture Fund (WVF).

{brand_context}

Your task: Recommend hashtags for this event:

**Event Details:**
- Title: {event.title}
- Date: {event.date}
- Topic: {event.description}
- Audience: {event.audience}

**Requirements:**
- Select 3-5 PRIMARY hashtags from WVF's official list (always include #WomensVentureFund)
- Suggest 5-7 TOPIC-SPECIFIC hashtags relevant to this event's content
- Avoid overly generic tags (#business, #success) — be specific
- Consider what NYC small business owners and entrepreneurs would search
- Explain your rationale (why these tags fit this event)

Return structured JSON matching the HashtagsOutput schema."""


NEWSLETTER_VARIANTS: dict[str, dict[str, str]] = {
    "standard": {
        "label": "Standard",
        "instructions": """- Opening hook (1-2 sentences — why this matters)
  * Event details in scannable format (date, time, speaker, what they'll learn)
  * 2-3 bullet points of key takeaways/benefits
  * Speaker credibility (1 sentence if relevant)
  * Clear CTA button text ("Register Now", "Save My Spot")
  * Closing encouragement (1 sentence)""",
    },
    "story_led": {
        "label": "Story-led",
        "instructions": """- Open with a short (2-3 sentence) narrative hook — a scenario an entrepreneur in the audience would recognize
  * Bridge from the story into the event details (date, time, speaker, what they'll learn)
  * 2-3 bullet points of key takeaways/benefits
  * Clear CTA button text ("Register Now", "Save My Spot")
  * Closing encouragement (1 sentence)""",
    },
    "faq_style": {
        "label": "FAQ-style",
        "instructions": """- Open with a 1-sentence hook
  * Present event details as 3-4 short Q&A pairs (e.g. "What will I learn?", "Who is this for?", "How do I register?")
  * Keep each answer to 1-2 sentences
  * Clear CTA button text ("Register Now", "Save My Spot")""",
    },
}


def build_newsletter_prompt(
    event: EventInput, variant: str = "standard", keymakers_stage_key: str | None = None
) -> str:
    """
    Build prompt for newsletter/email content.
    Follows nonprofit email best practices: clear subject, benefit-forward, scannable.

    `variant` selects a structural shape from NEWSLETTER_VARIANTS — ignored
    when `keymakers_stage_key` is set, since the Keymakers reference
    message supplies its own structure.

    `keymakers_stage_key`, when set, switches this into Keymakers
    recruitment-copy mode: Claude adapts the real Maria/WVF-approved
    reference message (see keymakers_campaign.py) for this event's
    specific details/audience, rather than writing generic event
    promotion. Raises KeyError via get_keymakers_stage_context() if the
    key is invalid, matching the pattern of unknown-variant errors below.
    """
    brand_context = get_brand_voice_context()

    if keymakers_stage_key:
        from app.services.keymakers_campaign import get_keymakers_stage_context

        keymakers_context = get_keymakers_stage_context(keymakers_stage_key)

        return f"""You are an email marketing specialist for Women's Venture Fund (WVF), a NYC CDFI supporting women entrepreneurs.

{brand_context}

{keymakers_context}

Your task: Adapt the reference message above into newsletter content, tailored to these specific event/audience details (but keep the reference message's core structure, tone, and central "What was your key?" framing intact — this is real approved-pending WVF campaign copy, not a generic template):

**Event/Audience Details:**
- Title: {event.title}
- Date: {event.date}
- Speaker: {event.speaker}
- Registration: {event.registration_link}
- Target Audience: {event.audience}
- Description: {event.description}

**Requirements:**
- Subject line: use one of the reference message's Subject options if provided, or write one in the same style if none were given
- Preview text: 50-100 chars, expands on subject
- Email body (HTML): adapt the reference message's body — same structure/flow, but weave in the event/audience details above where they fit naturally. Keep the [SHARE YOUR KEY] / [VISIT KEYMAKERS] style bracketed CTA markers as-is.
- Plain-text body: the same adapted content, reformatted as plain text (no tags, CTA rendered as "CTA text: URL" on its own line)
- Do NOT invent specifics the reference message and event details don't support (no fabricated stats, quotes, or dates)

Return structured JSON matching the NewsletterOutput schema."""

    structure = NEWSLETTER_VARIANTS[variant]["instructions"]

    return f"""You are an email marketing specialist for Women's Venture Fund (WVF), a NYC CDFI supporting women entrepreneurs.

{brand_context}

Your task: Write newsletter content for this event:

**Event Details:**
- Title: {event.title}
- Date: {event.date}
- Speaker: {event.speaker}
- Registration: {event.registration_link}
- Target Audience: {event.audience}
- Description: {event.description}

**Requirements:**
- Subject line: 40-60 chars, benefit-focused, creates urgency (e.g., "Free Workshop: Build Your Credit Score | July 16")
- Preview text: 50-100 chars, expands on subject (shows in inbox preview)
- Email body (HTML):
{structure}
- Plain-text body: the same content as the HTML body, reformatted as plain text (no tags, CTA rendered as "CTA text: URL" on its own line) — most ESPs require both an HTML and a plain-text part for deliverability
- Tone: warm, professional, benefit-forward (matching the brand examples)
- Keep total email under 200 words (people skim on mobile)

Return structured JSON matching the NewsletterOutput schema."""


def build_flyer_prompt(event: EventInput) -> str:
    """
    Build prompt for event flyer copy (text only — no graphic generation).
    Matches WVF's navy/sky-blue banner style conventions.
    """
    brand_context = get_brand_voice_context()

    return f"""You are a marketing designer writing flyer copy for Women's Venture Fund (WVF), a NYC-based CDFI supporting women entrepreneurs.

{brand_context}

Your task: Write flyer copy for this event (text only — no image will be generated):

**Event Details:**
- Title: {event.title}
- Date: {event.date}
- Speaker: {event.speaker}
- Registration: {event.registration_link}
- Target Audience: {event.audience}
- Description: {event.description}

**Requirements:**
- Headline: short, bold, attention-grabbing (fits a large flyer header, matches WVF's blocky headline style)
- Subheadline: one supporting line that adds context to the headline
- Body: scannable event details (what it is, who it's for, what they'll learn) — written for a printed/shared flyer, not a social caption
- CTA: short and action-driven (e.g. "Register Today", "Save Your Spot")
- Footer details: date, time, speaker, and registration link in a compact fine-print format

Return structured JSON matching the FlyerOutput schema."""


# ---------------------------------------------------------------------
# Newsletter blocks — the 6 modular sections from docs/PROJECT_CONTEXT.md
# Content Structure Guide. Each block is generated independently so staff
# can regenerate one section without touching the others, and so blocks
# can be swapped/dropped/reordered per issue per the PRD's flexibility
# note. See app/schemas/content.py for each block's output shape.
# ---------------------------------------------------------------------


def build_feature_article_prompt(event: EventInput) -> str:
    """Long-form educational article block, e.g. 'Contracting With the Government'."""
    brand_context = get_brand_voice_context()

    return f"""You are an editorial writer for Women's Venture Fund (WVF)'s newsletter, a NYC-based CDFI supporting women entrepreneurs.

{brand_context}

Your task: Write a long-form, educational feature article related to this event/topic:

**Event Details:**
- Title: {event.title}
- Description: {event.description}
- Target Audience: {event.audience}

**Requirements:**
- Headline: clear, benefit-forward
- Body: educational, long-form tone (like "Contracting With the Government") — teach the reader something useful related to the event topic, not just promote the event
- CTA text: short "Read More" style prompt
- Include a CTA link only if {event.registration_link} is directly relevant to the article; otherwise omit it

Return structured JSON matching the FeatureArticleBlock schema."""


def build_events_list_prompt(event: EventInput) -> str:
    """Bulleted upcoming-events block, sourced from event input data."""
    return f"""You are formatting an upcoming-events list for Women's Venture Fund (WVF)'s newsletter.

Your task: Create one events_list entry from this event's details (this block is designed to hold multiple events across a real newsletter issue — for this generation, produce exactly one entry for the event given):

**Event Details:**
- Title: {event.title}
- Date: {event.date}
- Speaker: {event.speaker}
- Registration: {event.registration_link}

**Requirements:**
- title: use the event title as given, cleaned up for scannability if needed
- date: extract just the date portion
- time: extract the time portion if present in the date string, otherwise omit
- registration_link: use the registration link as given

Return structured JSON matching the EventsListBlock schema, with `entries` containing exactly one item for this event."""


def build_grant_flyer_prompt(event: EventInput) -> str:
    """Repeatable grant/flyer entries block — where flyer copy actually lives."""
    brand_context = get_brand_voice_context()

    return f"""You are writing grant/funding opportunity copy for Women's Venture Fund (WVF)'s newsletter.

{brand_context}

Your task: Based on this event's context, draft ONE plausible, realistic grant/funding opportunity entry relevant to WVF's audience (NYC women entrepreneurs). If the event itself is about a specific grant or funding program, describe that one; otherwise draft a generic small-business grant opportunity consistent with WVF's mission.

**Event Context:**
- Title: {event.title}
- Description: {event.description}
- Audience: {event.audience}

**Requirements:**
- name: grant/program name
- amount: dollar amount or range
- deadline: a specific or relative deadline (e.g. "Rolling", "August 31, 2026")
- eligibility: 1 short sentence on who qualifies
- details_link: only include if {event.registration_link} is directly relevant, otherwise omit

Return structured JSON matching the GrantFlyerBlock schema, with `entries` containing exactly one item. NOTE: staff should replace this with real, verified grant details before publishing — this is a draft starting point, not verified funding information."""


def build_tips_cta_prompt(event: EventInput) -> str:
    """Short promotional headline + pitch block, reusable across issues."""
    brand_context = get_brand_voice_context()

    return f"""You are writing a short promotional tips/CTA block for Women's Venture Fund (WVF)'s newsletter.

{brand_context}

Your task: Write a short, benefit-forward promotional block encouraging readers to take advantage of WVF's business resources (training, mentorship, financial resources), tying in loosely with this event's theme where natural:

**Event Context:**
- Title: {event.title}
- Description: {event.description}

**Requirements:**
- headline: short, punchy promotional headline
- pitch: 1-2 sentence benefit-forward pitch
- image_prompt: describe an accompanying image matching WVF's visual pattern (navy/sky-blue block, bold white headline, logo watermark)

Return structured JSON matching the TipsCtaBlock schema."""


def build_member_spotlight_prompt(
    event: EventInput,
    key_maker_business_name: str | None = None,
    key_maker_owner_name: str | None = None,
    key_maker_business_type: str | None = None,
) -> str:
    """
    Key Maker testimonial block. Pass real Key Maker fields (from the
    key_makers table) when available; falls back to a clearly-labeled
    placeholder client when none is provided, per docs/PROJECT_CONTEXT.md
    ("build against placeholder data now, swap in real quotes once
    available" — testimonial quotes specifically still need Nancy's input
    even for real Key Makers, since none have been provided yet).
    """
    brand_context = get_brand_voice_context()

    if key_maker_business_name:
        client_context = f"""**Key Maker (real WVF client):**
- Business: {key_maker_business_name}
- Owner: {key_maker_owner_name or "N/A"}
- Business type: {key_maker_business_type or "N/A"}

NOTE: Write a plausible, respectful placeholder testimonial story for this real client. Do NOT invent specific quotes, dollar figures, or personal details attributed to them — use general, warm language about their business journey that Nancy/the client can review and replace with their actual testimonial."""
    else:
        client_context = """**Key Maker:** No specific client provided — write a generic, clearly-placeholder Key Maker spotlight (e.g. "A WVF Key Maker") that staff will swap with a real client's story."""

    return f"""You are writing a Member/Key Maker Spotlight block for Women's Venture Fund (WVF)'s newsletter — a feature on one of WVF's client success stories.

{brand_context}

{client_context}

**Event Context (for tone/theme alignment only):**
- Title: {event.title}
- Description: {event.description}

**Requirements:**
- headline: client story headline (e.g. "From Passion to Performance: [Business] Continues to Inspire")
- body: warm, community-focused story about the client's journey with WVF support — keep it general/placeholder as instructed above
- cta_text: short "Read More" style CTA

Return structured JSON matching the MemberSpotlightBlock schema."""


def build_boilerplate_prompt() -> str:
    """Static 'About WVF' + footer block — low generation priority, mostly reused across issues."""
    brand_context = get_brand_voice_context()

    return f"""You are writing the standard "About WVF" boilerplate footer block for Women's Venture Fund (WVF)'s newsletter.

{brand_context}

Your task: Write a short, reusable "About WVF" blurb (2-3 sentences) describing WVF's mission, suitable for reuse across every newsletter issue without changes.

**Requirements:**
- about_blurb: 2-3 sentence mission statement, warm and professional
- phone: use "(212) 563-0499" (WVF's published contact number)
- email: use "info@wvf-ny.org" (placeholder — confirm real contact email before publishing)
- website: use "www.womenventurefund.org" (placeholder — confirm real URL before publishing)

Return structured JSON matching the BoilerplateBlock schema."""


def build_calendar_prompt(event: EventInput, weeks: int = 2) -> str:
    """
    Build prompt for a multi-week content calendar promoting this event.
    Spreads posts across platforms with distinct angles per entry.
    """
    brand_context = get_brand_voice_context()

    return f"""You are a social media strategist building a content calendar for Women's Venture Fund (WVF).

{brand_context}

Your task: Build a {weeks}-week content calendar promoting this event:

**Event Details:**
- Title: {event.title}
- Date: {event.date}
- Speaker: {event.speaker}
- Registration: {event.registration_link}
- Target Audience: {event.audience}
- Description: {event.description}

**Requirements:**
- Cover {weeks} week(s) leading up to the event, with 3-5 posts per week (matching WVF's target posting frequency)
- Rotate across platforms (Instagram, LinkedIn, Facebook) — vary which platform each entry targets
- Vary the angle per entry: initial announcement, speaker spotlight, benefit/testimonial-style, reminder/urgency, day-of post
- Each entry needs its own short post idea, hashtags, and CTA — don't repeat the same post verbatim across entries
- Label each entry clearly (e.g. "Week 1, Monday")

Return structured JSON matching the ContentCalendarOutput schema, with `weeks` set to {weeks}."""


# Content types that currently support structural variants. Each maps to
# its `*_VARIANTS` dict above. Content types not listed here (hashtags,
# flyer, calendar) only have one shape today — add a *_VARIANTS dict and
# register it here when they need rotation too.
VARIANT_REGISTRY: dict[str, dict[str, dict[str, str]]] = {
    "social_post": SOCIAL_POST_VARIANTS,
    "newsletter": NEWSLETTER_VARIANTS,
}


def list_variants(content_type: str) -> dict[str, str]:
    """
    Returns {variant_key: label} for a content type, for populating a
    frontend dropdown. Empty dict if the content type has no variants.
    """
    return {key: v["label"] for key, v in VARIANT_REGISTRY.get(content_type, {}).items()}


# Variant keys excluded from "generate_new"/"avoid_recent" random pooling
# per content type — these are a different SELECTION AXIS than the random
# tone/structure rotation (e.g. platform for social_post: staff pick
# Instagram/LinkedIn/Facebook deliberately via their own dropdown, not by
# chance), so a random "generate new post" call should never silently land
# on one. Still selectable via an explicit variant key, same as any other
# variant — only the two random modes skip them.
RANDOM_POOL_EXCLUDED: dict[str, tuple[str, ...]] = {
    "social_post": SOCIAL_POST_PLATFORM_VARIANTS,
}


def resolve_variant(content_type: str, selection: str, recent_variants: list[str] | None = None) -> str:
    """
    Resolve a dropdown selection into a concrete variant key to pass into
    the matching build_*_prompt() function.

    `selection` is one of:
    - "generate_new": pick any available variant at random, EXCLUDING
      keys listed in RANDOM_POOL_EXCLUDED for this content_type (e.g.
      social_post's platform variants — those are a deliberate staff
      choice, not something a random rotation should land on by chance)
    - "avoid_recent": same random pool as "generate_new", further
      excluding variants in `recent_variants` (falls back to the full
      non-excluded pool if that would exclude all of them, e.g. caller
      has no history yet — this happens for every event until the
      database is wired up, see CLAUDE.md Status)
    - an explicit variant key (e.g. "listicle", or "facebook"): used as-is
      if valid, regardless of RANDOM_POOL_EXCLUDED — exclusion only
      affects the two random modes above, never explicit selection

    Content types with no registered variants always resolve to "standard"
    regardless of `selection`, since build_*_prompt() for those types
    doesn't take a variant argument in the first place.
    """
    variants = VARIANT_REGISTRY.get(content_type)
    if not variants:
        return "standard"

    keys = list(variants.keys())
    excluded = set(RANDOM_POOL_EXCLUDED.get(content_type, ()))
    random_pool = [k for k in keys if k not in excluded] or keys  # never empty-pool a content type

    if selection == "generate_new":
        return random.choice(random_pool)

    if selection == "avoid_recent":
        candidates = [k for k in random_pool if k not in (recent_variants or [])]
        return random.choice(candidates or random_pool)

    if selection in variants:
        return selection

    raise ValueError(
        f"Unknown variant '{selection}' for content_type '{content_type}'. "
        f"Valid options: 'generate_new', 'avoid_recent', or one of {keys}."
    )


def get_all_prompts(
    event: EventInput,
    social_post_variant: str = "standard",
    newsletter_variant: str = "standard",
    keymakers_stage_key: str | None = None,
) -> dict[str, str]:
    """
    Returns all prompts for parallel generation.

    social_post_variant / newsletter_variant should already be resolved via
    resolve_variant() — this function does not do selection itself.

    keymakers_stage_key, when set, switches the newsletter prompt into
    Keymakers recruitment-copy mode (see build_newsletter_prompt) —
    newsletter_variant is ignored in that case. Only the newsletter is
    affected; social_post/hashtags/flyer/calendar are unchanged, since the
    Keymakers reference copy is specifically an email/eblast campaign.
    """
    return {
        "social_post": build_social_post_prompt(event, social_post_variant),
        "hashtags": build_hashtags_prompt(event),
        "newsletter": build_newsletter_prompt(
            event, newsletter_variant, keymakers_stage_key=keymakers_stage_key
        ),
        "flyer": build_flyer_prompt(event),
        "calendar": build_calendar_prompt(event),
    }
