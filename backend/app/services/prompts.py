"""
Prompt templates for each content type.
Each function takes EventInput and returns a formatted prompt string.
"""

from app.schemas import EventInput
from app.services.brand_voice import get_brand_voice_context


def build_social_post_prompt(event: EventInput) -> str:
    """
    Build prompt for social media post generation.
    Target: under 150 words, includes CTA, uses brand hashtags.
    """
    brand_context = get_brand_voice_context()
    
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
- Keep caption under 150 words (2-3 short paragraphs)
- Lead with the benefit/hook (why should they care?)
- Include key details (date, time, what they'll learn)
- End with a clear CTA ("Register Now", "Save Your Spot", etc.)
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


def build_newsletter_prompt(event: EventInput) -> str:
    """
    Build prompt for newsletter/email content.
    Follows nonprofit email best practices: clear subject, benefit-forward, scannable.
    """
    brand_context = get_brand_voice_context()
    
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
  * Opening hook (1-2 sentences — why this matters)
  * Event details in scannable format (date, time, speaker, what they'll learn)
  * 2-3 bullet points of key takeaways/benefits
  * Speaker credibility (1 sentence if relevant)
  * Clear CTA button text ("Register Now", "Save My Spot")
  * Closing encouragement (1 sentence)
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


def get_all_prompts(event: EventInput) -> dict[str, str]:
    """
    Returns all prompts for parallel generation.
    """
    return {
        "social_post": build_social_post_prompt(event),
        "hashtags": build_hashtags_prompt(event),
        "newsletter": build_newsletter_prompt(event),
        "flyer": build_flyer_prompt(event),
        "calendar": build_calendar_prompt(event),
    }
