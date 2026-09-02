"""
Self-service "forgot passcode" flow for approvers (see
app/models/approver.py). Two endpoints:

1. POST /api/approvers/forgot-passcode — request a reset link, emailed
   to the approver's address on file.
2. POST /api/approvers/reset-passcode — consume that link's token to
   actually set a new passcode.

Neither endpoint reveals whether a given name/email corresponds to a
real approver — both return the same generic success response either
way, so this can't be used to enumerate approver names/emails.
"""

import logging
import secrets
from datetime import datetime, timedelta

import bcrypt
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Approver, PasscodeResetToken
from app.services import email_sender

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/approvers", tags=["approvers"])

RESET_TOKEN_MAX_AGE = timedelta(minutes=30)


def _get_frontend_url() -> str:
    import os

    url = os.getenv("FRONTEND_URL")
    if not url:
        raise ValueError("FRONTEND_URL environment variable not set")
    return url.rstrip("/")


class ForgotPasscodeRequest(BaseModel):
    approver_name: str


class GenericOkResponse(BaseModel):
    ok: bool = True


@router.post("/forgot-passcode", response_model=GenericOkResponse)
def forgot_passcode(request: ForgotPasscodeRequest, db: Session = Depends(get_db)) -> GenericOkResponse:
    """Looks up the approver by name and, if they have an email on file,
    emails them a one-time reset link. Always returns {"ok": true}
    regardless of whether the name matched a real approver or that
    approver has an email — never reveals which, so this can't be used
    to enumerate valid approver names."""
    approver = db.query(Approver).filter(Approver.name == request.approver_name).first()
    if approver and approver.email:
        raw_token = secrets.token_urlsafe(32)
        token_hash = bcrypt.hashpw(raw_token.encode(), bcrypt.gensalt()).decode()
        db.add(PasscodeResetToken(approver_id=approver.id, token_hash=token_hash))
        db.commit()

        reset_url = f"{_get_frontend_url()}/reset-passcode?token={raw_token}&approver={approver.id}"
        try:
            email_sender.send_passcode_reset_email(approver.email, approver.name, reset_url)
        except Exception:
            # Don't let an email-sending failure leak into the response —
            # log it for us to notice, but the caller still just sees ok.
            logger.exception("Failed to send passcode reset email for approver_id=%s", approver.id)

    return GenericOkResponse()


class ResetPasscodeRequest(BaseModel):
    approver_id: int
    token: str
    new_passcode: str


@router.post("/reset-passcode", response_model=GenericOkResponse)
def reset_passcode(request: ResetPasscodeRequest, db: Session = Depends(get_db)) -> GenericOkResponse:
    """Consumes a reset token (from the emailed link) to set a new
    passcode. Tokens are single-use and expire after RESET_TOKEN_MAX_AGE
    — checked here, not just cosmetically in the email copy."""
    candidates = (
        db.query(PasscodeResetToken)
        .filter(
            PasscodeResetToken.approver_id == request.approver_id,
            PasscodeResetToken.used_at.is_(None),
        )
        .order_by(PasscodeResetToken.created_at.desc())
        .all()
    )

    matching_token = None
    for candidate in candidates:
        if datetime.utcnow() - candidate.created_at > RESET_TOKEN_MAX_AGE:
            continue
        if bcrypt.checkpw(request.token.encode(), candidate.token_hash.encode()):
            matching_token = candidate
            break

    if not matching_token:
        raise HTTPException(status_code=400, detail="This reset link is invalid or has expired.")

    if len(request.new_passcode) < 6:
        raise HTTPException(status_code=422, detail="Passcode must be at least 6 characters.")

    approver = db.query(Approver).filter(Approver.id == request.approver_id).first()
    if not approver:
        raise HTTPException(status_code=404, detail="Approver not found")

    approver.passcode_hash = bcrypt.hashpw(request.new_passcode.encode(), bcrypt.gensalt()).decode()
    matching_token.used_at = datetime.utcnow()
    db.commit()

    return GenericOkResponse()
