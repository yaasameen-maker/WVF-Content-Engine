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
from app.schemas import EventInput, GeneratedContentResponse
from app.services.generation import generate_all_content
from app.services.prompts import list_variants

router = APIRouter(prefix="/api", tags=["generation"])

# How many past generations to look back at for "avoid_recent" selection.
RECENT_VARIANT_LOOKBACK = 5


class GenerateRequest(EventInput):
    """Request body for /api/generate: event fields (same shape as before)
    plus optional variant selections, so existing callers posting a bare
    EventInput still work unchanged. Selection values: "generate_new"
    (default), "avoid_recent", or an explicit variant key from
    GET /api/variants/{content_type}."""

    social_post_variant: str = Field(default="generate_new")
    newsletter_variant: str = Field(default="generate_new")


@router.get("/variants/{content_type}")
def get_variants(content_type: str) -> dict[str, str]:
    """List available structure variants for a content type, for a frontend
    dropdown. Returns {} for content types with no variants yet."""
    return list_variants(content_type)


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
    Generate all marketing content (social post, hashtags, newsletter) for an event.

    This endpoint:
    1. Takes event details from the form, plus optional structure-variant
       selections for social_post/newsletter
    2. Calls Claude API concurrently for all content types
    3. Persists the event and each generated content item (status=draft),
       recording which structure_variant was used where applicable
    4. Returns the structured JSON with all generated content
    """
    event = EventInput(**request.model_dump(exclude={"social_post_variant", "newsletter_variant"}))

    recent_social = _recent_variants(db, ContentType.SOCIAL_POST, RECENT_VARIANT_LOOKBACK)
    recent_newsletter = _recent_variants(db, ContentType.NEWSLETTER, RECENT_VARIANT_LOOKBACK)

    try:
        result, social_post_variant, newsletter_variant = await generate_all_content(
            event,
            social_post_variant_selection=request.social_post_variant,
            newsletter_variant_selection=request.newsletter_variant,
            recent_social_post_variants=recent_social,
            recent_newsletter_variants=recent_newsletter,
        )
    except ValueError as e:
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
                content_type=ContentType.SOCIAL_POST,
                body=result.social_post.model_dump_json(),
                structure_variant=social_post_variant,
            ),
            ContentItem(
                event_id=db_event.id,
                content_type=ContentType.HASHTAGS,
                body=result.hashtags.model_dump_json(),
            ),
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

    return result
