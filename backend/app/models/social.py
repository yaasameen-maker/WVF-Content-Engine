"""
Social platform OAuth connections — separate from content.py since this
is a distinct concern (publishing/auth, not content generation).

Scope decision: ONE shared connection per platform for the whole app, not
per-staff-member — there's no auth/user system built yet (see CLAUDE.md
Status), and this is one org's account (WVF's real X handle is
@WomensVFund — confirmed Aug 17, 2026), not a multi-tenant product. No
user_id column. If a real per-staff auth system gets built later, this
can gain a user_id/owner column then. The actual connected username is
always read dynamically from X at connect time (get_authenticated_user
in x_client.py), never hardcoded — so this comment being the real handle
doesn't matter functionally, just for accurate docs.

Manual-click only: this table and the routes that use it exist to support
a human clicking "Connect X" once and "Post to X" per item — never
automatic/scheduled posting. See docs/STATUS_AND_SCOPE.md's Aug 8 scope
decision. No queue, no scheduled_for field, on purpose.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum as SQLEnum
import enum

from app.database import Base


class SocialPlatform(str, enum.Enum):
    """Platforms with an OAuth connection. Only X is implemented today —
    the others are listed so future migrations can extend this enum
    rather than each platform inventing its own."""

    X = "x"


class SocialConnection(Base):
    """
    One row per connected platform account. At most one row per platform
    today (single shared WVF account, not per-user) — enforced at the
    application layer (upsert-by-platform), not a DB unique constraint,
    since a future per-user model would need multiple rows per platform.

    Tokens are stored encrypted (see app/services/token_encryption.py) —
    never plaintext, never logged.
    """

    __tablename__ = "social_connections"

    id = Column(Integer, primary_key=True, index=True)
    platform = Column(SQLEnum(SocialPlatform), nullable=False, index=True)
    platform_account_id = Column(String(255), nullable=False)
    username = Column(String(255), nullable=False)
    access_token_encrypted = Column(Text, nullable=False)
    refresh_token_encrypted = Column(Text, nullable=True)
    token_expires_at = Column(DateTime, nullable=True)
    scopes = Column(String(500), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<SocialConnection(platform={self.platform}, username={self.username!r})>"


class OAuthPkceState(Base):
    """
    Short-lived PKCE state for an in-progress OAuth connect flow — the
    gap between GET /api/oauth/x/start (redirects to X) and GET
    /api/oauth/x/callback (X redirects back with a code). Stored in the
    DB rather than a cookie/session, since this app has no session
    system yet and this needs to survive the round trip through X's
    servers even across a container restart. Deleted once consumed by
    the callback, or naturally orphaned/ignorable if abandoned (rows
    are keyed by a random state value, never reused, and small enough
    not to warrant a cleanup job at this app's volume).
    """

    __tablename__ = "oauth_pkce_states"

    id = Column(Integer, primary_key=True, index=True)
    platform = Column(SQLEnum(SocialPlatform), nullable=False, index=True)
    state = Column(String(255), nullable=False, unique=True, index=True)
    code_verifier = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class SocialPost(Base):
    """
    Record of a single manual-click publish attempt (success or failure)
    — for the review page to show "already posted" state and avoid
    accidental double-posts, and to keep an audit trail of what was
    actually published where.

    Not a queue/job table — created synchronously at the moment a human
    clicks "Post to X", not ahead of time.
    """

    __tablename__ = "social_posts"

    id = Column(Integer, primary_key=True, index=True)
    content_item_id = Column(Integer, ForeignKey("content_items.id"), nullable=False, index=True)
    platform = Column(SQLEnum(SocialPlatform), nullable=False, index=True)
    external_post_id = Column(String(255), nullable=True)
    status = Column(String(50), nullable=False)  # "success" | "failed"
    error_message = Column(Text, nullable=True)
    posted_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<SocialPost(platform={self.platform}, status={self.status!r})>"
