from datetime import datetime
from typing import Literal, Optional
from pydantic import BaseModel, Field


class EventInput(BaseModel):
    """Input schema matching the PRD form fields"""
    title: str = Field(..., description="Event title")
    date: str = Field(..., description="Event date")
    speaker: str = Field(..., description="Speaker name(s)")
    registration_link: str = Field(..., description="Registration URL")
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


class NewsletterOutput(BaseModel):
    """Newsletter/email content output"""
    subject_line: str = Field(..., description="Email subject line")
    preview_text: str = Field(..., description="Preview text (50-100 chars)")
    body: str = Field(..., description="Full email body HTML")
    cta_text: str = Field(..., description="Primary CTA button text")
    cta_link: str = Field(..., description="CTA destination URL")


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
    """Combined response from all content generators"""
    social_post: SocialPostOutput
    hashtags: HashtagsOutput
    newsletter: NewsletterOutput
    flyer: FlyerOutput
    calendar: ContentCalendarOutput


class ContentItemResponse(BaseModel):
    """A single persisted content item, as returned by CRUD endpoints"""
    id: int
    event_id: int
    content_type: str
    platform: Optional[str] = None
    status: str
    body: dict
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class EventResponse(BaseModel):
    """A persisted event, with input fields plus DB metadata"""
    id: int
    title: str
    date: str
    speaker: str
    registration_link: str
    audience: str
    description: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class EventWithContentResponse(EventResponse):
    """An event plus all of its generated content items"""
    content_items: list[ContentItemResponse] = Field(default_factory=list)


class ContentItemUpdate(BaseModel):
    """Fields a staff member can edit on a content item before approval"""
    body: Optional[dict] = None
    status: Optional[Literal["draft", "approved", "published"]] = None
