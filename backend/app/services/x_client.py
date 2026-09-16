"""
X (Twitter) API v2 client — OAuth 2.0 Authorization Code + PKCE flow and
tweet posting.

Manual-click only, per the confirmed Aug 8 scope decision (see
docs/STATUS_AND_SCOPE.md): this module only ever posts when a staff
member explicitly calls the publish endpoint. No queue, no scheduling,
no background posting.

Requires X_CLIENT_ID / X_CLIENT_SECRET (server-only env vars — never
exposed to the frontend). Callback URL must exactly match what's
registered in the X Developer Portal app settings.
"""

import asyncio
import base64
import hashlib
import os
import secrets

import httpx

X_AUTHORIZE_URL = "https://twitter.com/i/oauth2/authorize"
X_TOKEN_URL = "https://api.x.com/2/oauth2/token"
X_TWEETS_URL = "https://api.x.com/2/tweets"
X_ME_URL = "https://api.x.com/2/users/me"
X_MEDIA_UPLOAD_URL = "https://api.x.com/2/media/upload"
X_MEDIA_UPLOAD_INITIALIZE_URL = "https://api.x.com/2/media/upload/initialize"

# X's v2 media API is always chunked (INIT -> APPEND -> FINALIZE), even
# for a small image — there's no single-call shortcut, unlike the older
# v1.1 endpoint. A single APPEND segment must stay at or below 5MB per
# X's docs; the composer's 1080x1080 PNGs are well under that, so this
# module only ever sends one segment (index 0) rather than implementing
# multi-segment splitting.
X_MEDIA_APPEND_MAX_SEGMENT_BYTES = 5 * 1024 * 1024

# tweet.write lets the connected account publish; offline.access provides
# a refresh token so the connection survives past the initial token's
# expiry without asking staff to reconnect every time. media.write
# (added when image posting was wired up) is required by X's v2 media
# upload endpoint (see x_client.upload_media) — without it, uploading or
# attaching media to a tweet 403s even though tweet.write alone is
# enough for text-only posting. An X connection made BEFORE this scope
# was added needs to be disconnected and reconnected for its token to
# actually carry media.write — there's no way to add a scope to an
# already-issued token.
X_SCOPES = "tweet.read users.read tweet.write media.write offline.access"


def get_backend_url() -> str:
    """This FastAPI service's own public base URL (Railway) — the OAuth
    callback route (/api/oauth/x/callback) lives here, not on the
    frontend, so this must be the backend's domain, not Vercel's."""
    url = os.getenv("BACKEND_URL")
    if not url:
        raise ValueError(
            "BACKEND_URL environment variable not set — required to build the "
            "X OAuth callback URL (must exactly match the callback registered "
            "in the X Developer Portal app's OAuth 2.0 settings)."
        )
    return url.rstrip("/")


def get_frontend_url() -> str:
    """The Next.js frontend's base URL (Vercel) — used only to redirect
    the user's browser back to the app after the OAuth callback
    finishes. Never used to build the callback URL itself."""
    url = os.getenv("FRONTEND_URL")
    if not url:
        raise ValueError("FRONTEND_URL environment variable not set")
    return url.rstrip("/")


def get_redirect_uri() -> str:
    return f"{get_backend_url()}/api/oauth/x/callback"


def _get_client_id() -> str:
    client_id = os.getenv("X_CLIENT_ID")
    if not client_id:
        raise ValueError("X_CLIENT_ID environment variable not set")
    return client_id


def _get_client_secret() -> str:
    client_secret = os.getenv("X_CLIENT_SECRET")
    if not client_secret:
        raise ValueError("X_CLIENT_SECRET environment variable not set")
    return client_secret


def generate_pkce_pair() -> tuple[str, str]:
    """Returns (code_verifier, code_challenge) per RFC 7636 — code_verifier
    is stored server-side (see OAuthPkceState) and re-sent at token
    exchange; code_challenge is sent up front in the authorize URL."""
    code_verifier = secrets.token_urlsafe(64)[:128]
    digest = hashlib.sha256(code_verifier.encode("ascii")).digest()
    code_challenge = base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")
    return code_verifier, code_challenge


def generate_state() -> str:
    """Cryptographically random state value, checked at the callback to
    guard against CSRF — must round-trip unchanged through X's redirect."""
    return secrets.token_urlsafe(32)


def build_authorize_url(state: str, code_challenge: str) -> str:
    from urllib.parse import urlencode

    params = {
        "response_type": "code",
        "client_id": _get_client_id(),
        "redirect_uri": get_redirect_uri(),
        "scope": X_SCOPES,
        "state": state,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
    }
    return f"{X_AUTHORIZE_URL}?{urlencode(params)}"


async def exchange_code_for_tokens(code: str, code_verifier: str) -> dict:
    """
    Exchanges the authorization code from the callback for access/refresh
    tokens. X's OAuth 2.0 token endpoint uses HTTP Basic auth with
    client_id:client_secret (confidential client) per X's documented
    flow. Returns the raw token response dict (access_token,
    refresh_token, expires_in, scope, token_type).
    """
    auth = (_get_client_id(), _get_client_secret())
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": get_redirect_uri(),
        "code_verifier": code_verifier,
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(
            X_TOKEN_URL,
            data=data,
            auth=auth,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
    response.raise_for_status()
    return response.json()


async def refresh_access_token(refresh_token: str) -> dict:
    """Exchanges a stored refresh token for a new access token, when the
    stored access token has expired. Only called at publish time, never
    proactively/on a schedule."""
    auth = (_get_client_id(), _get_client_secret())
    data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(
            X_TOKEN_URL,
            data=data,
            auth=auth,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
    response.raise_for_status()
    return response.json()


async def get_authenticated_user(access_token: str) -> dict:
    """Fetches the connected account's own profile (id, username) right
    after connecting — used to populate SocialConnection.platform_account_id
    / username without staff having to type them in manually."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            X_ME_URL,
            headers={"Authorization": f"Bearer {access_token}"},
        )
    response.raise_for_status()
    return response.json()["data"]


async def upload_media(access_token: str, image_bytes: bytes, content_type: str) -> str:
    """
    Uploads image bytes to X and returns the resulting media_id, to be
    passed as media.media_ids in post_tweet(). Separate call from
    post_tweet() because X's API itself splits these into two calls —
    media must be uploaded first, then referenced by id in the tweet
    creation call.

    X's v2 media API is always a 3-step chunked flow — INIT, APPEND,
    FINALIZE — even for a small image; there is no single-call
    shortcut (unlike the older v1.1 endpoint, which this was originally
    written against and which 400'd against the real v2 API). This
    only ever sends one APPEND segment (index 0), since the composer's
    1080x1080 PNGs are well under the 5MB per-segment limit — true
    multi-segment splitting isn't implemented, since nothing in this
    app currently uploads anything larger.
    """
    if len(image_bytes) > X_MEDIA_APPEND_MAX_SEGMENT_BYTES:
        raise ValueError(
            f"Image is {len(image_bytes)} bytes, over the {X_MEDIA_APPEND_MAX_SEGMENT_BYTES}-byte "
            "single-segment limit this upload_media() implementation supports."
        )

    headers = {"Authorization": f"Bearer {access_token}"}

    async with httpx.AsyncClient() as client:
        init_response = await client.post(
            X_MEDIA_UPLOAD_INITIALIZE_URL,
            json={
                "media_type": content_type,
                "total_bytes": len(image_bytes),
                "media_category": "tweet_image",
            },
            headers={**headers, "Content-Type": "application/json"},
        )
        init_response.raise_for_status()
        media_id = init_response.json()["data"]["id"]

        append_response = await client.post(
            f"{X_MEDIA_UPLOAD_URL}/{media_id}/append",
            data={"segment_index": "0"},
            files={"media": ("image.png", image_bytes, content_type)},
            headers=headers,
        )
        append_response.raise_for_status()

        finalize_response = await client.post(
            f"{X_MEDIA_UPLOAD_URL}/{media_id}/finalize",
            headers=headers,
        )
        finalize_response.raise_for_status()
        finalize_data = finalize_response.json()["data"]

        # Images typically finalize immediately with no processing_info;
        # only poll STATUS if X actually says there's async processing
        # left to do (e.g. for video, which this app doesn't post today
        # but this loop costs nothing extra when it's skipped).
        processing_info = finalize_data.get("processing_info")
        while processing_info and processing_info.get("state") in ("pending", "in_progress"):
            await asyncio.sleep(processing_info.get("check_after_secs", 1))
            status_response = await client.get(
                X_MEDIA_UPLOAD_URL,
                params={"command": "STATUS", "media_id": media_id},
                headers=headers,
            )
            status_response.raise_for_status()
            status_data = status_response.json()["data"]
            processing_info = status_data.get("processing_info")
            if processing_info and processing_info.get("state") == "failed":
                raise RuntimeError(f"X media processing failed for media_id={media_id}: {processing_info}")

    return media_id


async def post_tweet(access_token: str, text: str, media_id: str | None = None) -> dict:
    """
    Publishes a single tweet, optionally with one attached image. Called
    ONLY when a staff member clicks "Post to X" on the review page —
    never from a queue or timer. Returns the raw X API response dict
    (data.id, data.text on success). media_id (from upload_media()) is
    optional — a content item with no saved composite still posts as
    text-only, same as before this existed.
    """
    payload: dict = {"text": text}
    if media_id:
        payload["media"] = {"media_ids": [media_id]}

    async with httpx.AsyncClient() as client:
        response = await client.post(
            X_TWEETS_URL,
            json=payload,
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            },
        )
    response.raise_for_status()
    return response.json()
