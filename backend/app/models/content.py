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
    event_id = Column(Integer, ForeignKey("events.id"), nullable=False, index=True)
    
    # Content metadata
    content_type = Column(SQLEnum(ContentType), nullable=False, index=True)
    platform = Column(String(50), nullable=True)  # Future: 'instagram', 'linkedin', 'facebook', etc.
    status = Column(SQLEnum(ContentStatus), default=ContentStatus.DRAFT, nullable=False, index=True)
    # Which structural variant was used (see app/services/prompts.py
    # VARIANT_REGISTRY). Null for content types with no variants yet.
    structure_variant = Column(String(50), nullable=True)
    
    # Content data (stored as JSON string)
    # For social_post: {"caption": "...", "hashtags": [...], "cta": "...", "suggested_image_prompt": "..."}
    # For newsletter: {"subject_line": "...", "preview_text": "...", "body": "...", "cta_text": "...", "cta_link": "..."}
    # For hashtags: {"primary_hashtags": [...], "topic_hashtags": [...], "rationale": "..."}
    body = Column(Text, nullable=False)  # JSON serialized content
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    event = relationship("Event", back_populates="content_items")
    
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
    testimonial_quote = Column(Text, nullable=True)  # placeholder until Nancy sends real quotes
    video_link = Column(String(500), nullable=True)
    photo_url = Column(String(500), nullable=True)

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
