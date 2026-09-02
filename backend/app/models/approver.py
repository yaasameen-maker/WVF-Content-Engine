"""
Named approver passcodes — separate from content.py since this is a
distinct concern (who's allowed to approve, not content generation).

Minimal stand-in for real auth: WVF has exactly two people who sign off
on content (Nancy, Maria — see docs/PROJECT_CONTEXT.md's single-approver
model, extended here to two named approvers). Rather than build a full
login system for two people, each gets a short passcode (bcrypt-hashed,
never stored or logged plaintext) they enter when clicking "Approve" —
enough to record who actually approved a piece of content, which matters
now that approval is the hard gate before scheduled auto-posting to X
(see app/routers/social.py's run_scheduled_x_posts).

Not a real user/session system: no login, no cookies, no roles beyond
"can approve." If a broader auth system gets built later (see CLAUDE.md
Status: "users.role exists in schema, no login yet"), this can be folded
into it then.
"""

from datetime import datetime
from sqlalchemy import Column, DateTime, Integer, String

from app.database import Base


class Approver(Base):
    """One named person authorized to approve content. Seeded manually
    (not self-service signup) — see backend/scripts or a one-off shell,
    not exposed via any public "create approver" API."""

    __tablename__ = "approvers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True)
    # bcrypt hash — the plaintext passcode is never stored, logged, or
    # returned by any endpoint after creation.
    passcode_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<Approver(id={self.id}, name={self.name!r})>"
