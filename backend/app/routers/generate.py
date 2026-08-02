"""
API router for content generation endpoints.
"""

import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import ContentItem, ContentType, Event
from app.schemas import EventInput, GeneratedContentResponse
from app.services.generation import generate_all_content

router = APIRouter(prefix="/api", tags=["generation"])


@router.post("/generate", response_model=GeneratedContentResponse)
async def generate_content(event: EventInput, db: Session = Depends(get_db)) -> GeneratedContentResponse:
    """
    Generate all marketing content (social post, hashtags, newsletter) for an event.

    This endpoint:
    1. Takes event details from the form
    2. Calls Claude API concurrently for all three content types
    3. Persists the event and each generated content item (status=draft)
    4. Returns the structured JSON with all generated content
    """
    try:
        result = await generate_all_content(event)
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
