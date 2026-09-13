"""
Media models — separate from content.py since these are a distinct
concern (raw/derived image assets, not generated text content). See
app/services/object_storage.py for how files actually get to Cloudflare
R2; these tables only ever store metadata, never file bytes.

Two tables, both proposed scope additions not yet approved by WVF:

- PhotoAsset: staff-uploaded raw photos (event photos, Key Maker
  headshots). Reverses nothing in CLAUDE.md directly, but shares its
  storage budget/account with the below.
- ComposedImage: a flattened photo+text-overlay PNG built client-side
  from a PhotoAsset plus a ContentItem's caption/headline, then uploaded
  the same direct-to-R2 way. This one IS a step beyond
  PROJECT_CONTEXT.md's "no image files generated or stored" line — see
  its own class docstring below.
"""

from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text

from app.database import Base

# Prefix used for composited-image object keys in R2 (see
# app/services/object_storage.py's build_object_key), mirroring "photos"
# below — kept here since ComposedImage is the only caller.
COMPOSED_IMAGE_OBJECT_PREFIX = "composed"


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


class ComposedImage(Base):
    """A flattened photo+text-overlay PNG generated client-side (browser
    Canvas — see the New Campaign photo-overlay step) from one PhotoAsset
    plus the caption/headline text of one ContentItem, then uploaded to
    R2 the same direct-to-storage way PhotoAsset is. This backend never
    receives or renders the composite itself — only the flattened PNG's
    bytes, already baked, land in R2; this row is just its metadata.

    Proposed scope addition, not yet approved by WVF — stacks on top of
    the (also unapproved) photo library, and is a step beyond
    PROJECT_CONTEXT.md's "Image Prompts: text descriptions only, no
    image files generated or stored" line. See that doc's Content
    Structure Guide for the visual pattern (navy/sky-blue block, bold
    white sans-serif headline) this is meant to approximate.

    One ContentItem can have multiple composites (e.g. staff tries a
    couple of layouts before picking one) — no uniqueness constraint on
    content_item_id. source_photo_id is nullable only because a
    PhotoAsset could later be deleted out from under an old composite;
    the flattened PNG itself has no dependency on the source photo row
    still existing.
    """

    __tablename__ = "content_composed_images"

    id = Column(Integer, primary_key=True, index=True)
    content_item_id = Column(Integer, ForeignKey("content_items.id", ondelete="CASCADE"), nullable=False, index=True)
    source_photo_id = Column(Integer, ForeignKey("photo_assets.id", ondelete="SET NULL"), nullable=True, index=True)
    object_key = Column(String(500), nullable=False, unique=True)
    public_url = Column(String(500), nullable=False)
    content_type = Column(String(100), nullable=False)
    size_bytes = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<ComposedImage(id={self.id}, content_item_id={self.content_item_id})>"
