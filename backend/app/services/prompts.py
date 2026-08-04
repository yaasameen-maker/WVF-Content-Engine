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
}


def build_social_post_prompt(event: EventInput, variant: str = "standard") -> str:
    """
    Build prompt for social media post generation.
    Target: under 150 words, includes CTA, uses brand hashtags.

    `variant` selects a structural shape from SOCIAL_POST_VARIANTS — see
    resolve_variant() for how callers should choose one (generate new /
    avoid recent repeats / explicit pick).
    """
    brand_context = get_brand_voice_context()
    structure = SOCIAL_POST_VARIANTS[variant]["instructions"]

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
- Match the tone from the examples: direct, benefit-forward, warm but professional
- Use emojis sparingly (🚨 for urgency, 📅 for dates, ✅ for benefits)

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


def build_newsletter_prompt(event: EventInput, variant: str = "standard") -> str:
    """
    Build prompt for newsletter/email content.
    Follows nonprofit email best practices: clear subject, benefit-forward, scannable.

    `variant` selects a structural shape from NEWSLETTER_VARIANTS.
    """
    brand_context = get_brand_voice_context()
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


def resolve_variant(content_type: str, selection: str, recent_variants: list[str] | None = None) -> str:
    """
    Resolve a dropdown selection into a concrete variant key to pass into
    the matching build_*_prompt() function.

    `selection` is one of:
    - "generate_new": pick any available variant at random
    - "avoid_recent": pick randomly from variants NOT in `recent_variants`
      (falls back to any variant if that would exclude all of them, e.g.
      caller has no history yet — this happens for every event until the
      database is wired up, see CLAUDE.md Status)
    - an explicit variant key (e.g. "listicle"): used as-is if valid

    Content types with no registered variants always resolve to "standard"
    regardless of `selection`, since build_*_prompt() for those types
    doesn't take a variant argument in the first place.
    """
    variants = VARIANT_REGISTRY.get(content_type)
    if not variants:
        return "standard"

    keys = list(variants.keys())

    if selection == "generate_new":
        return random.choice(keys)

    if selection == "avoid_recent":
        candidates = [k for k in keys if k not in (recent_variants or [])]
        return random.choice(candidates or keys)

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
) -> dict[str, str]:
    """
    Returns all prompts for parallel generation.

    social_post_variant / newsletter_variant should already be resolved via
    resolve_variant() — this function does not do selection itself.
    """
    return {
        "social_post": build_social_post_prompt(event, social_post_variant),
        "hashtags": build_hashtags_prompt(event),
        "newsletter": build_newsletter_prompt(event, newsletter_variant),
        "flyer": build_flyer_prompt(event),
        "calendar": build_calendar_prompt(event),
    }
