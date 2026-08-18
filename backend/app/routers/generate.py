"""
API router for content generation endpoints.
"""

import json
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import ContentItem, ContentType, Event
from app.schemas import ContentItemResponse, EventInput, GeneratedContentResponse, HashtagsOutput, SocialPostVariant
from app.services.generation import generate_all_content
from app.services.instagram_templates import get_instagram_template, list_instagram_templates
from app.services.keymakers_campaign import get_keymakers_stage, list_keymakers_stages
from app.services.prompts import list_variants
from app.services.x_templates import get_x_template, list_x_templates

router = APIRouter(prefix="/api", tags=["generation"])

# How many past generations to look back at for "avoid_recent" selection.
RECENT_VARIANT_LOOKBACK = 5


class GenerateRequest(EventInput):
    """Request body for /api/generate: event fields (same shape as before)
    plus optional generation options, so existing callers posting a bare
    EventInput still work unchanged.

    social_post_platform: optional. When set (instagram/linkedin/facebook/
    x/tiktok), all 3 social post options in the batch stay on that platform, varying
    only the opening angle — see generate_social_post_variants(). When
    unset, the 3 options use the fixed tone variants instead. Social posts
    no longer support "avoid_recent"/explicit single-variant selection —
    every generation returns all 3 tone variants (or all 3 angles, if a
    platform is set) for staff to compare on the review page.

    newsletter_variant: "generate_new" (default), "avoid_recent", or an
    explicit variant key from GET /api/variants/newsletter — unchanged,
    the newsletter is still single-generation.

    keymakers_stage_key: optional. When set, the newsletter is generated
    by adapting the selected real Keymakers recruitment reference message
    (see GET /api/keymakers-stages) instead of the normal event-promotion
    newsletter — newsletter_variant is ignored when this is set."""

    social_post_platform: Optional[str] = Field(default=None)
    newsletter_variant: str = Field(default="generate_new")
    keymakers_stage_key: Optional[str] = Field(default=None)


@router.get("/variants/{content_type}")
def get_variants(content_type: str) -> dict[str, str]:
    """List available structure variants for a content type, for a frontend
    dropdown. Returns {} for content types with no variants yet."""
    return list_variants(content_type)


@router.get("/keymakers-stages")
def get_keymakers_stages() -> dict[str, str]:
    """List available Keymakers recruitment-campaign stages ({stage_key:
    label}), for the newsletter form's Keymakers toggle dropdown."""
    return list_keymakers_stages()


class KeymakersStageDetail(BaseModel):
    """One Keymakers stage's full real reference copy — for a frontend
    that renders the message directly (e.g. an instant static-template
    view), rather than list_keymakers_stages()'s {key: label} dropdown
    shape or build_newsletter_prompt()'s formatted prompt-injection
    string."""

    label: str
    audience: str
    stage: str
    send_day: int
    subject_options: Optional[list[str]] = None
    body: str


@router.get("/keymakers-stages/{stage_key}", response_model=KeymakersStageDetail)
def get_keymakers_stage_detail(stage_key: str) -> KeymakersStageDetail:
    """Get one Keymakers stage's full real reference copy (label, audience,
    subject line options, and body) — the actual WVF campaign message
    text, for direct display rather than AI generation."""
    try:
        return KeymakersStageDetail(**get_keymakers_stage(stage_key))
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/instagram-templates")
def get_instagram_templates() -> dict[str, str]:
    """List available real Instagram post templates ({template_key:
    label}), for the event form's Instagram Fixed-template picker."""
    return list_instagram_templates()


class InstagramTemplateDetail(BaseModel):
    """One real Instagram template's full content — for a frontend that
    renders it directly (Fixed template mode), no AI call involved.
    truncated=True means the source screenshot cut off part of the real
    caption (e.g. a shortened/scrolled URL) — the frontend should warn
    staff to double-check before sending, rather than presenting it as
    complete."""

    label: str
    category: str
    caption: str
    hashtags: list[str]
    truncated: bool = False


@router.get("/instagram-templates/{template_key}", response_model=InstagramTemplateDetail)
def get_instagram_template_detail(template_key: str) -> InstagramTemplateDetail:
    """Get one real, published WVF Instagram post's full caption and
    hashtags — for direct display/editing rather than AI generation."""
    try:
        return InstagramTemplateDetail(**get_instagram_template(template_key))
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/x-templates")
def get_x_templates() -> dict[str, str]:
    """List available real X post templates ({template_key: label}), for
    the event form's X Fixed-template picker."""
    return list_x_templates()


class XTemplateDetail(BaseModel):
    """One real X template's full content — for a frontend that renders
    it directly (Fixed template mode), no AI call involved. See
    InstagramTemplateDetail.truncated for what truncated=True means."""

    label: str
    category: str
    caption: str
    hashtags: list[str]
    truncated: bool = False


@router.get("/x-templates/{template_key}", response_model=XTemplateDetail)
def get_x_template_detail(template_key: str) -> XTemplateDetail:
    """Get one real, published WVF X post's full caption and hashtags —
    for direct display/editing rather than AI generation."""
    try:
        return XTemplateDetail(**get_x_template(template_key))
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))


def _recent_variants(db: Session, content_type: ContentType, limit: int) -> list[str]:
    """Most recent non-null structure_variant values used for a content
    type, most recent first — used to drive "avoid_recent" selection."""
    rows = (
        db.query(ContentItem.structure_variant)
        .filter(ContentItem.content_type == content_type)
        .filter(ContentItem.structure_variant.isnot(None))
        .order_by(desc(ContentItem.created_at))
        .limit(limit)
        .all()
    )
    return [r[0] for r in rows]


@router.post("/generate", response_model=GeneratedContentResponse)
async def generate_content(
    request: GenerateRequest, db: Session = Depends(get_db)
) -> GeneratedContentResponse:
    """
    Generate all marketing content for an event.

    This endpoint:
    1. Takes event details from the form, plus optional generation options
       (social_post_platform, newsletter_variant, keymakers_stage_key)
    2. Calls Claude API concurrently for all content types — social post
       and hashtags each come back as SOCIAL_POST_VARIANT_COUNT options
       (see generate_social_post_variants) for staff to compare
    3. Persists the event, plus the newsletter/flyer/calendar content items
       (status=draft) immediately, same as before. Social post and
       hashtags are NOT persisted yet — see POST
       /api/content/select-social-variant, called once staff picks one on
       the review page.
    4. Returns the structured JSON with all generated content plus the
       event_id needed for that later pick-and-persist call.
    """
    event = EventInput(
        **request.model_dump(
            exclude={"social_post_platform", "newsletter_variant", "keymakers_stage_key"}
        )
    )

    recent_newsletter = _recent_variants(db, ContentType.NEWSLETTER, RECENT_VARIANT_LOOKBACK)

    try:
        result, newsletter_variant = await generate_all_content(
            event,
            social_post_platform=request.social_post_platform,
            newsletter_variant_selection=request.newsletter_variant,
            recent_newsletter_variants=recent_newsletter,
            keymakers_stage_key=request.keymakers_stage_key,
        )
    except (ValueError, KeyError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")

    db_event = Event(
        title=event.title,
        date=event.date,
        speaker=event.speaker,
        registration_link=event.registration_link,
        audience=event.audience,
        description=event.description,
    )
    db.add(db_event)
    db.flush()

    db.add_all(
        [
            ContentItem(
                event_id=db_event.id,
                content_type=ContentType.NEWSLETTER,
                body=result.newsletter.model_dump_json(),
                structure_variant=newsletter_variant,
            ),
            ContentItem(
                event_id=db_event.id,
                content_type=ContentType.FLYER,
                body=result.flyer.model_dump_json(),
            ),
            ContentItem(
                event_id=db_event.id,
                content_type=ContentType.CALENDAR,
                body=result.calendar.model_dump_json(),
            ),
        ]
    )
    db.commit()

    result.event_id = db_event.id
    return result


class SelectSocialVariantRequest(BaseModel):
    """Body for POST /api/content/select-social-variant: the event this
    content belongs to, plus the exact SocialPostVariant + HashtagsOutput
    the staff member picked (echoed back from the /api/generate response
    they were shown — this endpoint doesn't re-run generation, it only
    persists a choice)."""

    event_id: int
    social_post_variant: SocialPostVariant
    hashtags: HashtagsOutput


@router.post("/content/select-social-variant", response_model=list[ContentItemResponse])
def select_social_variant(
    request: SelectSocialVariantRequest, db: Session = Depends(get_db)
) -> list[ContentItemResponse]:
    """
    Persist the social post + hashtags option staff picked from the
    3-variant batch returned by /api/generate. Must be called exactly once
    per event — social_post/hashtags ContentItems don't exist until this
    runs, unlike newsletter/flyer/calendar which are saved at generate time.
    """
    event = db.query(Event).filter(Event.id == request.event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    social_post_item = ContentItem(
        event_id=event.id,
        content_type=ContentType.SOCIAL_POST,
        body=request.social_post_variant.post.model_dump_json(),
        structure_variant=request.social_post_variant.structure_variant,
    )
    hashtags_item = ContentItem(
        event_id=event.id,
        content_type=ContentType.HASHTAGS,
        body=request.hashtags.model_dump_json(),
    )
    db.add_all([social_post_item, hashtags_item])
    db.commit()
    db.refresh(social_post_item)
    db.refresh(hashtags_item)

    # ContentItem.body is stored as a JSON string (see ContentItem.body
    # docstring in app/models/content.py) — must be parsed back to a dict
    # before handing to ContentItemResponse, same as
    # app/routers/content.py's _serialize_content_item does.
    def _to_response(item: ContentItem) -> ContentItemResponse:
        return ContentItemResponse(
            id=item.id,
            event_id=item.event_id,
            key_maker_id=item.key_maker_id,
            content_type=item.content_type.value,
            block_type=item.block_type.value if item.block_type else None,
            platform=item.platform,
            status=item.status.value,
            structure_variant=item.structure_variant,
            body=json.loads(item.body),
            created_at=item.created_at,
            updated_at=item.updated_at,
        )

    return [_to_response(social_post_item), _to_response(hashtags_item)]
