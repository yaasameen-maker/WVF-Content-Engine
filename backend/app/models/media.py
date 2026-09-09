"""
Staff-uploaded photo library — separate from content.py since this is a
distinct concern (raw uploaded material, not generated content). See
app/services/object_storage.py for how files actually get to Cloudflare
R2; this table only ever stores metadata, never file bytes.

Proposed scope addition, not yet approved by WVF — see the "Photo
Library" phase in the image-generation/photo-library plan. Reverses
nothing in CLAUDE.md directly (unlike AI image generation), but shares
its storage budget/account.
"""

from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text

from app.database import Base


class PhotoAsset(Base):
    """One staff-uploaded photo (event photos, Key Maker headshots,
    etc.), available for the AI to reference when generating images
    (see app/services/image_generation.py) or for staff to browse/pick
    from manually. key_maker_id/event_id are both optional — a photo
    doesn't need to be tagged to anything to exist in the library,
    mirroring ContentItem.event_id's own "optional association" pattern."""

    __tablename__ = "photo_assets"

    id = Column(Integer, primary_key=True, index=True)
    object_key = Column(String(500), nullable=False, unique=True)
    public_url = Column(String(500), nullable=False)
    filename = Column(String(255), nullable=False)
    content_type = Column(String(100), nullable=False)
    size_bytes = Column(Integer, nullable=False)
    key_maker_id = Column(Integer, ForeignKey("key_makers.id"), nullable=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=True, index=True)
    caption = Column(Text, nullable=True)
    # Free-text name, not a FK to approvers/users — there's no login
    # system for general staff (only approvers get passcodes), so this
    # is informational only, same rationale as ContentItem not tracking
    # created_by beyond what the review UI already shows.
    uploaded_by = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<PhotoAsset(id={self.id}, filename={self.filename!r})>"
