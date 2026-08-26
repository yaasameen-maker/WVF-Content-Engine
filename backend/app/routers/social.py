"""
X account connection (OAuth 2.0 + PKCE) and manual-click publishing.

Manual-click only — see docs/STATUS_AND_SCOPE.md's Aug 8 scope decision.
Every route here either sets up/completes an OAuth connect flow a human
initiated, or publishes a single post because a human clicked a button.
Nothing here runs on a timer or queue.

Single shared WVF connection per platform, not per-user — see
app/models/social.py's SocialConnection docstring for why.
"""

import json
import logging
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import ContentItem, ContentStatus, ContentType, OAuthPkceState, SocialConnection, SocialPlatform, SocialPost
from app.services import meta_client, x_client
from app.services.token_encryption import decrypt_token, encrypt_token

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["social"])

# PKCE state rows older than this are considered abandoned — a stale
# state showing up at the callback (e.g. a bookmarked/reused link) is
# rejected rather than trusted indefinitely.
PKCE_STATE_MAX_AGE = timedelta(minutes=10)


@router.get("/oauth/x/start")
def start_x_oauth(db: Session = Depends(get_db)) -> RedirectResponse:
    """
    Step 1 of the connect flow: a staff member clicks "Connect X" in the
    frontend, which links here. Generates PKCE state, stores it, and
    redirects to X's authorization screen.
    """
    code_verifier, code_challenge = x_client.generate_pkce_pair()
    state = x_client.generate_state()

    db.add(
        OAuthPkceState(
            platform=SocialPlatform.X,
            state=state,
            code_verifier=code_verifier,
        )
    )
    db.commit()

    authorize_url = x_client.build_authorize_url(state, code_challenge)
    return RedirectResponse(url=authorize_url)


@router.get("/oauth/x/callback")
async def x_oauth_callback(
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
    db: Session = Depends(get_db),
) -> RedirectResponse:
    """
    Step 2: X redirects here with either an authorization code (success)
    or an error (user declined, etc). Validates state, exchanges the
    code for tokens, fetches the connected account's identity, and
    upserts the one SocialConnection row for X.
    """
    frontend_url = x_client.get_frontend_url()

    if error:
        return RedirectResponse(url=f"{frontend_url}/?x_connect=error&reason={error}")

    if not code or not state:
        return RedirectResponse(url=f"{frontend_url}/?x_connect=error&reason=missing_params")

    pkce_row = db.query(OAuthPkceState).filter(OAuthPkceState.state == state).first()
    if not pkce_row:
        return RedirectResponse(url=f"{frontend_url}/?x_connect=error&reason=invalid_state")

    if datetime.utcnow() - pkce_row.created_at > PKCE_STATE_MAX_AGE:
        db.delete(pkce_row)
        db.commit()
        return RedirectResponse(url=f"{frontend_url}/?x_connect=error&reason=expired_state")

    code_verifier = pkce_row.code_verifier
    # Consume the state immediately — one-time use, whether or not the
    # rest of the exchange succeeds, so a replayed callback can't retry.
    db.delete(pkce_row)
    db.commit()

    try:
        tokens = await x_client.exchange_code_for_tokens(code, code_verifier)
        user = await x_client.get_authenticated_user(tokens["access_token"])
    except Exception:
        logger.exception("X OAuth token exchange failed")
        return RedirectResponse(url=f"{frontend_url}/?x_connect=error&reason=token_exchange_failed")

    expires_in = tokens.get("expires_in")
    token_expires_at = (
        datetime.utcnow() + timedelta(seconds=expires_in) if expires_in else None
    )

    existing = db.query(SocialConnection).filter(SocialConnection.platform == SocialPlatform.X).first()
    if existing:
        existing.platform_account_id = user["id"]
        existing.username = user["username"]
        existing.access_token_encrypted = encrypt_token(tokens["access_token"])
        existing.refresh_token_encrypted = (
            encrypt_token(tokens["refresh_token"]) if tokens.get("refresh_token") else None
        )
        existing.token_expires_at = token_expires_at
        existing.scopes = tokens.get("scope")
    else:
        db.add(
            SocialConnection(
                platform=SocialPlatform.X,
                platform_account_id=user["id"],
                username=user["username"],
                access_token_encrypted=encrypt_token(tokens["access_token"]),
                refresh_token_encrypted=(
                    encrypt_token(tokens["refresh_token"]) if tokens.get("refresh_token") else None
                ),
                token_expires_at=token_expires_at,
                scopes=tokens.get("scope"),
            )
        )
    db.commit()

    return RedirectResponse(url=f"{frontend_url}/?x_connect=success")


class XConnectionStatus(BaseModel):
    connected: bool
    username: str | None = None


@router.get("/social/x/status", response_model=XConnectionStatus)
def get_x_connection_status(db: Session = Depends(get_db)) -> XConnectionStatus:
    """Whether X is connected, for the frontend to show Connect/Connected
    state — never exposes tokens."""
    connection = db.query(SocialConnection).filter(SocialConnection.platform == SocialPlatform.X).first()
    if not connection:
        return XConnectionStatus(connected=False)
    return XConnectionStatus(connected=True, username=connection.username)


@router.delete("/social/x/connection")
def disconnect_x(db: Session = Depends(get_db)) -> dict:
    """Removes the stored X connection — the "disconnect account" action
    every OAuth integration needs. Does not revoke the token with X
    itself (X's API supports this, but isn't wired up here yet); staff
    can additionally revoke access from X's own app-permissions settings
    if needed."""
    connection = db.query(SocialConnection).filter(SocialConnection.platform == SocialPlatform.X).first()
    if not connection:
        raise HTTPException(status_code=404, detail="No X connection to disconnect")
    db.delete(connection)
    db.commit()
    return {"disconnected": True}


# ---------------------------------------------------------------------
# Meta (Instagram + Facebook) — one OAuth dialog covers both, since a
# Facebook Login grant exposes whichever Pages the user manages and
# whichever Instagram Business account is linked to each Page. See
# app/services/meta_client.py's module docstring: connecting works today,
# but publishing will 403 until WVF's Meta app passes App Review.
# ---------------------------------------------------------------------


@router.get("/oauth/meta/start")
def start_meta_oauth(db: Session = Depends(get_db)) -> RedirectResponse:
    """Step 1: a staff member clicks "Connect Instagram" or "Connect
    Facebook" — both land here, since Meta's login dialog isn't
    platform-specific. Uses SocialPlatform.FACEBOOK as the PKCE state
    row's platform value (arbitrary choice between the two Meta
    platforms — code_verifier is unused for Meta's flow, which has no
    PKCE, but OAuthPkceState is reused here rather than adding a
    second state-tracking table for one extra column)."""
    state = x_client.generate_state()
    db.add(
        OAuthPkceState(
            platform=SocialPlatform.FACEBOOK,
            state=state,
            code_verifier="unused-meta-has-no-pkce",
        )
    )
    db.commit()

    authorize_url = meta_client.build_authorize_url(state)
    return RedirectResponse(url=authorize_url)


@router.get("/oauth/meta/callback")
async def meta_oauth_callback(
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
    db: Session = Depends(get_db),
) -> RedirectResponse:
    """Step 2: Meta redirects here with a code. Exchanges it for a
    long-lived user token, lists the Pages the user manages, and stores a
    FACEBOOK connection for the (first, or only) Page plus an INSTAGRAM
    connection if that Page has a linked IG Business account. WVF has one
    real Page, so "first" is the practical choice rather than building a
    picker UI for an org with only one Page to pick from."""
    frontend_url = meta_client.get_frontend_url()

    if error:
        return RedirectResponse(url=f"{frontend_url}/?meta_connect=error&reason={error}")
    if not code or not state:
        return RedirectResponse(url=f"{frontend_url}/?meta_connect=error&reason=missing_params")

    pkce_row = db.query(OAuthPkceState).filter(OAuthPkceState.state == state).first()
    if not pkce_row:
        return RedirectResponse(url=f"{frontend_url}/?meta_connect=error&reason=invalid_state")
    if datetime.utcnow() - pkce_row.created_at > PKCE_STATE_MAX_AGE:
        db.delete(pkce_row)
        db.commit()
        return RedirectResponse(url=f"{frontend_url}/?meta_connect=error&reason=expired_state")

    db.delete(pkce_row)
    db.commit()

    try:
        short_lived = await meta_client.exchange_code_for_user_token(code)
        long_lived = await meta_client.exchange_for_long_lived_token(short_lived["access_token"])
        pages = await meta_client.get_managed_pages(long_lived["access_token"])
    except Exception:
        logger.exception("Meta OAuth token exchange failed")
        return RedirectResponse(url=f"{frontend_url}/?meta_connect=error&reason=token_exchange_failed")

    if not pages:
        return RedirectResponse(url=f"{frontend_url}/?meta_connect=error&reason=no_pages_found")

    page = pages[0]
    page_token_expires_at = None  # Page tokens derived from a long-lived user token don't expire on their own

    existing_fb = db.query(SocialConnection).filter(SocialConnection.platform == SocialPlatform.FACEBOOK).first()
    if existing_fb:
        existing_fb.platform_account_id = page["id"]
        existing_fb.username = page["name"]
        existing_fb.access_token_encrypted = encrypt_token(page["access_token"])
        existing_fb.token_expires_at = page_token_expires_at
    else:
        db.add(
            SocialConnection(
                platform=SocialPlatform.FACEBOOK,
                platform_account_id=page["id"],
                username=page["name"],
                access_token_encrypted=encrypt_token(page["access_token"]),
                token_expires_at=page_token_expires_at,
            )
        )

    ig_account = page.get("instagram_business_account")
    if ig_account:
        existing_ig = (
            db.query(SocialConnection).filter(SocialConnection.platform == SocialPlatform.INSTAGRAM).first()
        )
        if existing_ig:
            existing_ig.platform_account_id = ig_account["id"]
            existing_ig.username = page["name"]  # IG username needs a separate Graph call; Page name stands in for now
            existing_ig.access_token_encrypted = encrypt_token(page["access_token"])
            existing_ig.token_expires_at = page_token_expires_at
        else:
            db.add(
                SocialConnection(
                    platform=SocialPlatform.INSTAGRAM,
                    platform_account_id=ig_account["id"],
                    username=page["name"],
                    access_token_encrypted=encrypt_token(page["access_token"]),
                    token_expires_at=page_token_expires_at,
                )
            )

    db.commit()
    return RedirectResponse(url=f"{frontend_url}/?meta_connect=success")


class MetaConnectionStatus(BaseModel):
    connected: bool
    username: str | None = None


@router.get("/social/instagram/status", response_model=MetaConnectionStatus)
def get_instagram_connection_status(db: Session = Depends(get_db)) -> MetaConnectionStatus:
    connection = (
        db.query(SocialConnection).filter(SocialConnection.platform == SocialPlatform.INSTAGRAM).first()
    )
    if not connection:
        return MetaConnectionStatus(connected=False)
    return MetaConnectionStatus(connected=True, username=connection.username)


@router.delete("/social/instagram/connection")
def disconnect_instagram(db: Session = Depends(get_db)) -> dict:
    connection = (
        db.query(SocialConnection).filter(SocialConnection.platform == SocialPlatform.INSTAGRAM).first()
    )
    if not connection:
        raise HTTPException(status_code=404, detail="No Instagram connection to disconnect")
    db.delete(connection)
    db.commit()
    return {"disconnected": True}


@router.get("/social/facebook/status", response_model=MetaConnectionStatus)
def get_facebook_connection_status(db: Session = Depends(get_db)) -> MetaConnectionStatus:
    connection = (
        db.query(SocialConnection).filter(SocialConnection.platform == SocialPlatform.FACEBOOK).first()
    )
    if not connection:
        return MetaConnectionStatus(connected=False)
    return MetaConnectionStatus(connected=True, username=connection.username)


@router.delete("/social/facebook/connection")
def disconnect_facebook(db: Session = Depends(get_db)) -> dict:
    connection = (
        db.query(SocialConnection).filter(SocialConnection.platform == SocialPlatform.FACEBOOK).first()
    )
    if not connection:
        raise HTTPException(status_code=404, detail="No Facebook connection to disconnect")
    db.delete(connection)
    db.commit()
    return {"disconnected": True}


async def _get_valid_x_access_token(db: Session, connection: SocialConnection) -> str:
    """Returns a usable access token, refreshing first if the stored one
    has expired. Only called at the moment of a manual publish click —
    never proactively."""
    if connection.token_expires_at and datetime.utcnow() >= connection.token_expires_at:
        if not connection.refresh_token_encrypted:
            raise HTTPException(
                status_code=409,
                detail="X access token expired and no refresh token is stored — reconnect the account.",
            )
        refresh_token = decrypt_token(connection.refresh_token_encrypted)
        tokens = await x_client.refresh_access_token(refresh_token)
        connection.access_token_encrypted = encrypt_token(tokens["access_token"])
        if tokens.get("refresh_token"):
            connection.refresh_token_encrypted = encrypt_token(tokens["refresh_token"])
        expires_in = tokens.get("expires_in")
        connection.token_expires_at = (
            datetime.utcnow() + timedelta(seconds=expires_in) if expires_in else None
        )
        db.commit()

    return decrypt_token(connection.access_token_encrypted)


class PostToXRequest(BaseModel):
    content_item_id: int


class PostToXResponse(BaseModel):
    external_post_id: str
    status: str


@router.post("/social/x/post", response_model=PostToXResponse)
async def post_to_x(request: PostToXRequest, db: Session = Depends(get_db)) -> PostToXResponse:
    """
    Publishes an existing social_post ContentItem to X. Called ONLY when
    a staff member clicks "Post to X" on the review page — this is the
    manual-click publish action, not a queued/scheduled job.
    """
    connection = db.query(SocialConnection).filter(SocialConnection.platform == SocialPlatform.X).first()
    if not connection:
        raise HTTPException(status_code=409, detail="X is not connected — connect it first.")

    item = db.query(ContentItem).filter(ContentItem.id == request.content_item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Content item not found")
    if item.content_type != ContentType.SOCIAL_POST:
        raise HTTPException(status_code=400, detail="Content item is not a social post")

    body = json.loads(item.body)
    caption = body.get("caption")
    if not caption:
        raise HTTPException(status_code=400, detail="This content item has no caption to post")

    try:
        access_token = await _get_valid_x_access_token(db, connection)
        result = await x_client.post_tweet(access_token, caption)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("X publish failed for content_item_id=%s", request.content_item_id)
        db.add(
            SocialPost(
                content_item_id=item.id,
                platform=SocialPlatform.X,
                status="failed",
                error_message=str(e),
            )
        )
        db.commit()
        raise HTTPException(status_code=502, detail=f"X publish failed: {e}")

    external_post_id = result["data"]["id"]
    db.add(
        SocialPost(
            content_item_id=item.id,
            platform=SocialPlatform.X,
            external_post_id=external_post_id,
            status="success",
        )
    )
    item.status = ContentStatus.PUBLISHED
    db.commit()

    return PostToXResponse(external_post_id=external_post_id, status="success")
