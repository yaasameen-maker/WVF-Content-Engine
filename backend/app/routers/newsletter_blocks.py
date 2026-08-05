"""
API router for newsletter block generation — the 6 modular sections from
docs/PROJECT_CONTEXT.md Content Structure Guide, kept separate from
/api/generate so staff can generate/regenerate individual blocks without
paying for all 5 event-driven content types every time.
"""

import json
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import ContentItem, ContentType, Event, KeyMaker, NewsletterBlockType
from app.services.generation import NEWSLETTER_BLOCK_GENERATORS, generate_newsletter_blocks
from app.schemas import EventInput

router = APIRouter(prefix="/api", tags=["newsletter-blocks"])

ALL_BLOCK_TYPES = list(NEWSLETTER_BLOCK_GENERATORS.keys())


class NewsletterBlocksRequest(BaseModel):
    """
    Request body for /api/newsletter-blocks.

    Either `event_id` (reuse an existing event's details) or `event` (fresh
    event details, e.g. for blocks not really tied to a specific past
    event like boilerplate) must be provided. `block_types` defaults to all
    six but callers can request a subset, since the PRD says blocks may be
    swapped/dropped/reordered per issue rather than always generating all
    six every time.
    """

    event_id: Optional[int] = None
    event: Optional[EventInput] = None
    block_types: list[str] = Field(default_factory=lambda: list(ALL_BLOCK_TYPES))
    # Only used when 'member_spotlight' is in block_types. If omitted, the
    # spotlight is generated as a generic placeholder.
    key_maker_id: Optional[int] = None


class NewsletterBlockResult(BaseModel):
    """One generated+persisted block in the response."""

    id: int
    block_type: str
    body: dict


@router.get("/newsletter-blocks/types")
def list_block_types() -> list[str]:
    """List the valid newsletter block type keys, for a frontend block picker."""
    return ALL_BLOCK_TYPES


@router.post("/newsletter-blocks", response_model=list[NewsletterBlockResult])
async def generate_and_persist_newsletter_blocks(
    request: NewsletterBlocksRequest, db: Session = Depends(get_db)
) -> list[NewsletterBlockResult]:
    """
    Generate the requested newsletter blocks and persist each as its own
    content_items row (content_type='newsletter_block', status='draft').
    """
    unknown = set(request.block_types) - set(ALL_BLOCK_TYPES)
    if unknown:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown block type(s): {sorted(unknown)}. Valid options: {ALL_BLOCK_TYPES}",
        )

    if request.event_id is not None:
        db_event = db.query(Event).filter(Event.id == request.event_id).first()
        if not db_event:
            raise HTTPException(status_code=404, detail="Event not found")
        event = EventInput(
            title=db_event.title,
            date=db_event.date,
            speaker=db_event.speaker,
            registration_link=db_event.registration_link,
            audience=db_event.audience,
            description=db_event.description,
        )
    elif request.event is not None:
        event = request.event
        db_event = None
    else:
        raise HTTPException(status_code=400, detail="Either event_id or event must be provided")

    key_maker = None
    if "member_spotlight" in request.block_types and request.key_maker_id is not None:
        key_maker = db.query(KeyMaker).filter(KeyMaker.id == request.key_maker_id).first()
        if not key_maker:
            raise HTTPException(status_code=404, detail="Key Maker not found")

    try:
        blocks = await generate_newsletter_blocks(
            event,
            request.block_types,
            key_maker_business_name=key_maker.business_name if key_maker else None,
            key_maker_owner_name=key_maker.owner_name if key_maker else None,
            key_maker_business_type=key_maker.business_type if key_maker else None,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")

    content_items = []
    for block_type, block_output in blocks.items():
        item = ContentItem(
            event_id=db_event.id if db_event else None,
            key_maker_id=key_maker.id if (key_maker and block_type == "member_spotlight") else None,
            content_type=ContentType.NEWSLETTER_BLOCK,
            block_type=NewsletterBlockType(block_type),
            body=block_output.model_dump_json(),
        )
        db.add(item)
        content_items.append((block_type, item))

    db.commit()
    for _, item in content_items:
        db.refresh(item)

    return [
        NewsletterBlockResult(id=item.id, block_type=block_type, body=json.loads(item.body))
        for block_type, item in content_items
    ]
