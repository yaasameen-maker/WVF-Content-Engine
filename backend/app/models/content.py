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
