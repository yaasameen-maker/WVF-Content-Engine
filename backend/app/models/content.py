"""
SQLAlchemy models for the WVF Content Engine.

Architecture decision (from sprint plan):
- `events` table: Stores event details (input from the form)
- `content_items` table: Stores generated content pieces with status tracking
  
This "generation vs. state" split allows:
- One event can have multiple content variations
- Independent editing of each content type (social/newsletter/hashtags)
- Status tracking per content piece (draft → approved → published)
"""

from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    ForeignKey,
    Enum as SQLEnum,
)
from sqlalchemy.orm import relationship
import enum

from app.database import Base


class ContentStatus(str, enum.Enum):
    """Status workflow for content items"""
    DRAFT = "draft"
    APPROVED = "approved"
    PUBLISHED = "published"


class ContentType(str, enum.Enum):
    """Types of generated content"""
    SOCIAL_POST = "social_post"
    HASHTAGS = "hashtags"
    NEWSLETTER = "newsletter"
    FLYER = "flyer"  # Future
    IMAGE_PROMPT = "image_prompt"  # Future
    CALENDAR = "calendar"  # Future
    NEWSLETTER_BLOCK = "newsletter_block"


class NewsletterBlockType(str, enum.Enum):
    """
    The 6 modular newsletter sections, per docs/PROJECT_CONTEXT.md Content
    Structure Guide. Only set when content_type == NEWSLETTER_BLOCK.
    """
    FEATURE_ARTICLE = "feature_article"
    EVENTS_LIST = "events_list"
    GRANT_FLYER = "grant_flyer"
    TIPS_CTA = "tips_cta"
    MEMBER_SPOTLIGHT = "member_spotlight"
    BOILERPLATE = "boilerplate"


class Event(Base):
    """
    Events table - stores input data from the event form.
    One event can generate multiple content items.
    """
    __tablename__ = "events"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    date = Column(String(100), nullable=False)  # Stored as string for flexibility
    speaker = Column(String(255), nullable=False)
    registration_link = Column(String(500), nullable=False)
    audience = Column(Text, nullable=False)
    description = Column(Text, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    content_items = relationship("ContentItem", back_populates="event", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Event(id={self.id}, title='{self.title}')>"


class ContentItem(Base):
    """
    Content items table - stores generated marketing content.
    Each item:
    - Belongs to one event
    - Has a specific type (social_post, newsletter, etc.)
    - Tracks status (draft, approved, published)
    - Stores content as JSON for structured data
    """
    __tablename__ = "content_items"

    id = Column(Integer, primary_key=True, index=True)
    # Nullable: most content_items are generated "for" one event, but some
    # newsletter_block rows (boilerplate, grant_flyer, member_spotlight)
    # are reused across issues and aren't tied to a single event.
    event_id = Column(Integer, ForeignKey("events.id"), nullable=True, index=True)
    # Only set when content_type == NEWSLETTER_BLOCK and block_type ==
    # MEMBER_SPOTLIGHT — which real Key Maker this spotlight is about.
    key_maker_id = Column(Integer, ForeignKey("key_makers.id"), nullable=True, index=True)

    # Content metadata
    content_type = Column(SQLEnum(ContentType), nullable=False, index=True)
    # Only set when content_type == NEWSLETTER_BLOCK — which of the 6
    # modular newsletter sections this row is (see NewsletterBlockType).
    block_type = Column(SQLEnum(NewsletterBlockType), nullable=True, index=True)
    platform = Column(String(50), nullable=True)  # Future: 'instagram', 'linkedin', 'facebook', etc.
    status = Column(SQLEnum(ContentStatus), default=ContentStatus.DRAFT, nullable=False, index=True)
    # Which structural variant was used (see app/services/prompts.py
    # VARIANT_REGISTRY). Null for content types with no variants yet.
    structure_variant = Column(String(50), nullable=True)

    # Content data (stored as JSON string)
    # For social_post: {"caption": "...", "hashtags": [...], "cta": "...", "suggested_image_prompt": "..."}
    # For newsletter: {"subject_line": "...", "preview_text": "...", "body": "...", "cta_text": "...", "cta_link": "..."}
    # For hashtags: {"primary_hashtags": [...], "topic_hashtags": [...], "rationale": "..."}
    # For newsletter_block: shape varies by block_type — see app/schemas/content.py
    body = Column(Text, nullable=False)  # JSON serialized content

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    event = relationship("Event", back_populates="content_items")
    key_maker = relationship("KeyMaker")

    def __repr__(self):
        return f"<ContentItem(id={self.id}, type={self.content_type}, status={self.status})>"


class KeyMaker(Base):
    """
    WVF's 10 client testimonial subjects for the Member Spotlight newsletter
    block (see docs/PROJECT_CONTEXT.md — distinct from Felix's 4 GHL
    personas). Only public-facing fields live here: business name, owner
    name, business type, and public website/social links WVF already
    publishes about these clients. Personal phone numbers, personal emails,
    and unconfirmed addresses are deliberately NOT modeled here — see
    backend/seed_key_makers_public.py and CLAUDE.md for why.
    """
    __tablename__ = "key_makers"

    id = Column(Integer, primary_key=True, index=True)
    business_name = Column(String(255), nullable=False)
    owner_name = Column(String(255), nullable=False)
    business_type = Column(String(255), nullable=True)
    website = Column(String(500), nullable=True)
    social_media = Column(Text, nullable=True)  # freeform: "Instagram: ...; Facebook: ..."
    testimonial_quote = Column(Text, nullable=True)  # short pull-quote; placeholder until provided
    video_link = Column(String(500), nullable=True)
    photo_url = Column(String(500), nullable=True)

    # Full bio content, added Aug 2026 once real testimonial/story content
    # started arriving per-Key-Maker (see docs/PROJECT_CONTEXT.md Action
    # Items). All nullable — most Key Makers still only have the public
    # fields above; the Profiles page shows "Bio pending" until these are
    # populated. title/location/industry are short facts; key_quotes is a
    # JSON-serialized list[str] (see ContentItem.body for the same
    # JSON-in-Text convention used elsewhere in this codebase — no native
    # JSON column type); story is the full narrative bio text.
    title = Column(String(255), nullable=True)
    location = Column(String(255), nullable=True)
    industry = Column(String(255), nullable=True)
    key_quotes = Column(Text, nullable=True)  # JSON-serialized list[str]
    story = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<KeyMaker(id={self.id}, business_name='{self.business_name}')>"


class KeyMakerPrivate(Base):
    """
    Sensitive Key Maker contact/coordination data (phone, email, address,
    internal team notes) kept in a SEPARATE table from KeyMaker so the
    public model/seed file never touches PII. This table's schema is
    committed to git (it's just column definitions), but it is only ever
    populated by backend/seed_key_makers_private.py, which is gitignored
    and must never be committed. See CLAUDE.md for the reasoning.
    """
    __tablename__ = "key_makers_private"

    id = Column(Integer, primary_key=True, index=True)
    key_maker_id = Column(Integer, ForeignKey("key_makers.id"), nullable=False, unique=True, index=True)
    phone = Column(String(50), nullable=True)
    email = Column(String(255), nullable=True)
    address = Column(Text, nullable=True)
    team_notes = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<KeyMakerPrivate(id={self.id}, key_maker_id={self.key_maker_id})>"
