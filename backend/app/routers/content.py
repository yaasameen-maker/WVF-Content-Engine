"""
CRUD endpoints for events and their generated content items.
"""

import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models import ContentItem, ContentStatus, Event, KeyMaker
from app.schemas import ContentItemResponse, ContentItemUpdate, EventWithContentResponse, KeyMakerResponse

router = APIRouter(prefix="/api", tags=["content"])


def _serialize_content_item(item: ContentItem) -> ContentItemResponse:
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


def _serialize_event(event: Event) -> EventWithContentResponse:
    return EventWithContentResponse(
        id=event.id,
        title=event.title,
        date=event.date,
        speaker=event.speaker,
        registration_link=event.registration_link,
        audience=event.audience,
        description=event.description,
        created_at=event.created_at,
        updated_at=event.updated_at,
        content_items=[_serialize_content_item(item) for item in event.content_items],
    )


@router.get("/events", response_model=list[EventWithContentResponse])
def list_events(db: Session = Depends(get_db)) -> list[EventWithContentResponse]:
    """List all events with their generated content items, newest first."""
    events = (
        db.query(Event)
        .options(joinedload(Event.content_items))
        .order_by(Event.created_at.desc())
        .all()
    )
    return [_serialize_event(e) for e in events]


@router.get("/events/{event_id}", response_model=EventWithContentResponse)
def get_event(event_id: int, db: Session = Depends(get_db)) -> EventWithContentResponse:
    """Get a single event with all of its generated content items."""
    event = (
        db.query(Event)
        .options(joinedload(Event.content_items))
        .filter(Event.id == event_id)
        .first()
    )
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return _serialize_event(event)


def _serialize_key_maker(key_maker: KeyMaker) -> KeyMakerResponse:
    return KeyMakerResponse(
        id=key_maker.id,
        business_name=key_maker.business_name,
        owner_name=key_maker.owner_name,
        business_type=key_maker.business_type,
        website=key_maker.website,
        social_media=key_maker.social_media,
        testimonial_quote=key_maker.testimonial_quote,
        video_link=key_maker.video_link,
        photo_url=key_maker.photo_url,
    )


@router.get("/key-makers", response_model=list[KeyMakerResponse])
def list_key_makers(db: Session = Depends(get_db)) -> list[KeyMakerResponse]:
    """List all Key Makers' public profile fields, alphabetical by business name."""
    key_makers = db.query(KeyMaker).order_by(KeyMaker.business_name.asc()).all()
    return [_serialize_key_maker(k) for k in key_makers]


@router.get("/key-makers/{key_maker_id}", response_model=KeyMakerResponse)
def get_key_maker(key_maker_id: int, db: Session = Depends(get_db)) -> KeyMakerResponse:
    """Get a single Key Maker's public profile fields."""
    key_maker = db.query(KeyMaker).filter(KeyMaker.id == key_maker_id).first()
    if not key_maker:
        raise HTTPException(status_code=404, detail="Key Maker not found")
    return _serialize_key_maker(key_maker)


@router.get("/content/{content_id}", response_model=ContentItemResponse)
def get_content_item(content_id: int, db: Session = Depends(get_db)) -> ContentItemResponse:
    """Get a single content item."""
    item = db.query(ContentItem).filter(ContentItem.id == content_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Content item not found")
    return _serialize_content_item(item)


@router.patch("/content/{content_id}", response_model=ContentItemResponse)
def update_content_item(
    content_id: int, update: ContentItemUpdate, db: Session = Depends(get_db)
) -> ContentItemResponse:
    """Update a content item's body (staff edits) and/or status."""
    item = db.query(ContentItem).filter(ContentItem.id == content_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Content item not found")

    if update.body is not None:
        item.body = json.dumps(update.body)
    if update.status is not None:
        item.status = ContentStatus(update.status)

    db.commit()
    db.refresh(item)
    return _serialize_content_item(item)


@router.post("/content/{content_id}/approve", response_model=ContentItemResponse)
def approve_content_item(content_id: int, db: Session = Depends(get_db)) -> ContentItemResponse:
    """Mark a content item as approved."""
    item = db.query(ContentItem).filter(ContentItem.id == content_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Content item not found")

    item.status = ContentStatus.APPROVED
    db.commit()
    db.refresh(item)
    return _serialize_content_item(item)
