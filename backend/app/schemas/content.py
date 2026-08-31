from datetime import datetime
from typing import Literal, Optional
from pydantic import BaseModel, Field


class EventInput(BaseModel):
    """Input schema matching the PRD form fields"""
    title: str = Field(..., description="Event title")
    date: str = Field(..., description="Event date")
    speaker: str = Field(..., description="Speaker name(s)")
    # Optional (Aug 2026): a link isn't always ready at generation time —
    # staff can add it later by editing the generated copy. Prompts omit
    # the registration CTA/link entirely when this is unset.
    registration_link: Optional[str] = Field(default=None, description="Registration URL, if known yet")
    audience: str = Field(..., description="Target audience")
    description: str = Field(..., description="Event description")


class SocialPostOutput(BaseModel):
    """Structured social media post output"""
    caption: str = Field(..., description="Post caption (under 150 words)")
    hashtags: list[str] = Field(..., description="Relevant hashtags")
    suggested_image_prompt: str = Field(..., description="DALL-E style image prompt")
    cta: str = Field(..., description="Call-to-action text")


class HashtagsOutput(BaseModel):
    """Standalone hashtag recommendations"""
    primary_hashtags: list[str] = Field(..., description="3-5 primary brand hashtags")
    topic_hashtags: list[str] = Field(..., description="5-7 topic-specific hashtags")
    rationale: str = Field(..., description="Why these tags fit the event")


class SocialPostVariant(BaseModel):
    """One social post option within a 3-variant generation batch. Wraps
    SocialPostOutput plus the structure_variant key it used (e.g.
    "standard"/"listicle"/"quote_style", or a platform key when a platform
    was explicitly selected), so the picked one can be persisted with the
    same structure_variant tracking every other social_post gets."""
    structure_variant: str
    structure_label: str = Field(..., description="Human-readable label for the variant, e.g. 'Listicle'")
    post: SocialPostOutput


class HashtagsVariant(BaseModel):
    """One hashtag-set option within a 3-variant generation batch, paired
    1:1 by index with the SocialPostVariant it was generated alongside
    (both draw on the same event details; hashtags aren't independently
    keyed to a structure_variant the way social posts are)."""
    hashtags: HashtagsOutput


class NewsletterOutput(BaseModel):
    """Newsletter/email content output"""
    subject_line: str = Field(..., description="Email subject line")
    preview_text: str = Field(..., description="Preview text (50-100 chars)")
    body: str = Field(..., description="Full email body HTML")
    body_plain_text: str = Field(
        ..., description="Plain-text version of the email body, for ESPs that require both HTML and text parts"
    )
    cta_text: str = Field(..., description="Primary CTA button text")
    # Optional (Aug 2026): when the event has no registration_link yet,
    # there's no real URL to put here — the prompt instructs Claude to
    # return null rather than invent a placeholder (previously observed:
    # a literal "<UNKNOWN>" string leaking into real output).
    cta_link: Optional[str] = Field(default=None, description="CTA destination URL, if known yet")


class FlyerOutput(BaseModel):
    """Event flyer copy output (text only — no graphic generation)"""
    headline: str = Field(..., description="Large flyer headline, short and punchy")
    subheadline: str = Field(..., description="Supporting line under the headline")
    body: str = Field(..., description="Flyer body copy — event details in scannable format")
    cta: str = Field(..., description="Call-to-action text, e.g. 'Register Today'")
    footer_details: str = Field(..., description="Fine print: date/time/location/registration link")


class CalendarPostEntry(BaseModel):
    """A single scheduled post within a content calendar"""
    day_label: str = Field(..., description="e.g. 'Week 1, Monday'")
    platform: str = Field(..., description="e.g. 'Instagram', 'LinkedIn', 'Facebook'")
    post_idea: str = Field(..., description="Short description of what this post covers")
    hashtags: list[str] = Field(..., description="Hashtags for this specific post")
    cta: str = Field(..., description="Call-to-action for this post")


class ContentCalendarOutput(BaseModel):
    """Multi-week content calendar output"""
    weeks: int = Field(..., description="Number of weeks this calendar covers")
    entries: list[CalendarPostEntry] = Field(..., description="Scheduled posts across the calendar period")


class GeneratedContentResponse(BaseModel):
    """Combined response from all content generators.

    event_id: the persisted Event row this content was generated for.
    None immediately after generate_all_content() runs (the Event row is
    created by the /api/generate route handler afterward, using the
    already-generated content) — the route handler sets this before
    returning. Always non-None in the actual HTTP response; the caller
    must pass it back to POST /api/content/select-social-variant once
    staff picks a variant, since social_post/hashtags are NOT persisted as
    ContentItems until that pick happens (see below).

    social_post_variants / hashtags_variants are parallel lists (same
    length, same index = generated together) — staff compares them on the
    review page and picks one; only the picked pair gets persisted as a
    ContentItem (see POST /api/content/select-social-variant). Every other
    field here is still single-generation and persisted immediately, same
    as before."""
    event_id: Optional[int] = None
    social_post_variants: list[SocialPostVariant]
    hashtags_variants: list[HashtagsVariant]
    newsletter: NewsletterOutput
    flyer: FlyerOutput
    calendar: ContentCalendarOutput


# ---------------------------------------------------------------------
# Newsletter blocks — the 6 modular sections from docs/PROJECT_CONTEXT.md
# Content Structure Guide. Each has its own output shape; content_type is
# always 'newsletter_block' on the persisted ContentItem, with block_type
# distinguishing which of these six it is.
# ---------------------------------------------------------------------


class FeatureArticleBlock(BaseModel):
    """Long-form educational article block"""
    headline: str = Field(..., description="Article headline")
    body: str = Field(..., description="Article body copy")
    cta_text: str = Field(..., description="'Read More' style CTA text")
    cta_link: Optional[str] = Field(None, description="CTA destination URL, if any")


class EventListEntry(BaseModel):
    """A single entry in the events_list block"""
    title: str
    date: str
    time: Optional[str] = None
    registration_link: Optional[str] = None


class EventsListBlock(BaseModel):
    """Bulleted upcoming-events block, sourced from event input data"""
    entries: list[EventListEntry] = Field(..., description="Upcoming events, most imminent first")


class GrantEntry(BaseModel):
    """A single repeatable grant/flyer entry"""
    name: str
    amount: str
    deadline: str
    eligibility: str
    details_link: Optional[str] = None


class GrantFlyerBlock(BaseModel):
    """Repeatable grant/flyer entries — where flyer copy actually lives"""
    entries: list[GrantEntry] = Field(..., description="Grant/flyer opportunities")


class TipsCtaBlock(BaseModel):
    """Short promotional headline + pitch block"""
    headline: str = Field(..., description="Promotional headline")
    pitch: str = Field(..., description="Short benefit-forward pitch")
    image_prompt: Optional[str] = Field(
        None, description="Text description of the accompanying image, matching WVF's visual pattern"
    )


class MemberSpotlightBlock(BaseModel):
    """Key Maker testimonial block"""
    key_maker_id: Optional[int] = Field(None, description="Linked KeyMaker row, once real data is available")
    headline: str = Field(..., description="Client story headline")
    body: str = Field(..., description="Testimonial/story body copy")
    cta_text: str = Field(..., description="'Read More' style CTA text")
    cta_link: Optional[str] = Field(None, description="CTA destination URL, if any")


class BoilerplateBlock(BaseModel):
    """Static 'About WVF' + footer block — low generation priority, mostly reused"""
    about_blurb: str = Field(..., description="'About WVF' boilerplate text")
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None


# Maps block_type string -> its output schema, for generic validation.
NEWSLETTER_BLOCK_SCHEMAS: dict[str, type[BaseModel]] = {
    "feature_article": FeatureArticleBlock,
    "events_list": EventsListBlock,
    "grant_flyer": GrantFlyerBlock,
    "tips_cta": TipsCtaBlock,
    "member_spotlight": MemberSpotlightBlock,
    "boilerplate": BoilerplateBlock,
}


class ContentItemResponse(BaseModel):
    """A single persisted content item, as returned by CRUD endpoints"""
    id: int
    event_id: Optional[int] = None
    key_maker_id: Optional[int] = None
    content_type: str
    block_type: Optional[str] = None
    platform: Optional[str] = None
    status: str
    structure_variant: Optional[str] = None
    body: dict
    # Staff-set target publish date shown on /calendar — see
    # ContentItem.scheduled_date's model comment. Null falls back to the
    # parent event's own date on the calendar view.
    scheduled_date: Optional[str] = None
    # Optional free-text time-of-day reminder (e.g. "2:30 PM") — display
    # only, see ContentItem.scheduled_time's model comment.
    scheduled_time: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class EventResponse(BaseModel):
    """A persisted event, with input fields plus DB metadata"""
    id: int
    title: str
    date: str
    speaker: str
    registration_link: Optional[str] = None
    audience: str
    description: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class EventWithContentResponse(EventResponse):
    """An event plus all of its generated content items"""
    content_items: list[ContentItemResponse] = Field(default_factory=list)


class KeyMakerResponse(BaseModel):
    """A single Key Maker's PUBLIC profile fields only — mirrors the
    KeyMaker model exactly, never KeyMakerPrivate (phone/email/address),
    which has no API exposure by design. See app/models/content.py's
    KeyMaker/KeyMakerPrivate docstrings for the PII-safety reasoning.

    Full bio fields (title/location/industry/key_quotes/story) were added
    Aug 2026 once real per-Key-Maker testimonial content started arriving
    — only 4 of the 10 real Key Makers have this populated so far (see
    seed_key_makers_public.py). None here means "bio not yet available,"
    not blank — the frontend must render that state explicitly, never as
    empty text, and never fabricate placeholder content."""

    id: int
    business_name: str
    owner_name: str
    business_type: Optional[str] = None
    website: Optional[str] = None
    social_media: Optional[str] = None
    testimonial_quote: Optional[str] = None
    video_link: Optional[str] = None
    photo_url: Optional[str] = None
    title: Optional[str] = None
    location: Optional[str] = None
    industry: Optional[str] = None
    key_quotes: Optional[list[str]] = None
    story: Optional[str] = None

    model_config = {"from_attributes": True}


class ContentItemUpdate(BaseModel):
    """Fields a staff member can edit on a content item before approval"""
    body: Optional[dict] = None
    status: Optional[Literal["draft", "approved", "published"]] = None
    scheduled_date: Optional[str] = None
    scheduled_time: Optional[str] = None
