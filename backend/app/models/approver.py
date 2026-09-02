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
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String

from app.database import Base


class Approver(Base):
    """One named person authorized to approve content. Seeded manually
    (not self-service signup) — see backend/manage_approvers.py, not
    exposed via any public "create approver" API.

    email (Sept 2026) enables self-service passcode reset (see
    PasscodeResetToken below) — an approver who forgets their passcode
    clicks "Forgot passcode?" on the Approve form and gets a one-time
    reset link, instead of needing Claude/a dev to run manage_approvers.py
    reset against production every time."""

    __tablename__ = "approvers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True)
    # Nullable: an approver created before this field existed, or created
    # via manage_approvers.py without one, simply can't use self-service
    # reset — manage_approvers.py reset still works for them regardless.
    email = Column(String(255), nullable=True, unique=True)
    # bcrypt hash — the plaintext passcode is never stored, logged, or
    # returned by any endpoint after creation.
    passcode_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<Approver(id={self.id}, name={self.name!r})>"


class PasscodeResetToken(Base):
    """A single-use, short-lived token for the self-service "forgot
    passcode" flow (see routers/approvers.py). Stored hashed (bcrypt) so
    a DB read alone can't be used to reset someone's passcode — same
    reasoning as OAuthPkceState's state values, but hashed since this
    token is emailed out and a leaked email is a more plausible exposure
    than a leaked in-memory OAuth redirect."""

    __tablename__ = "passcode_reset_tokens"

    id = Column(Integer, primary_key=True, index=True)
    approver_id = Column(Integer, ForeignKey("approvers.id"), nullable=False, index=True)
    token_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    # Set once the token is used — a used token is never valid again,
    # even before it would otherwise expire.
    used_at = Column(DateTime, nullable=True)
