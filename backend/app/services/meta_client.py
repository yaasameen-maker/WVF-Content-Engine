"""
Meta Graph API client — shared by Instagram and Facebook, since both go
through the same Facebook Login OAuth flow and the same underlying app.

Manual-click only, same scope decision as x_client.py (see
docs/STATUS_AND_SCOPE.md's Aug 8 scope decision): only ever posts when a
staff member explicitly clicks "Post to Instagram"/"Post to Facebook".

STATUS (Aug 2026): OAuth code path is built and this is what the
"Connect Instagram"/"Connect Facebook" buttons call, but publishing will
return a permission error until WVF's Meta Developer app passes App
Review for `pages_manage_posts` / `instagram_content_publish` — that's a
manual approval process on Meta's side (can take days to weeks once
submitted), not something fixable in code. Connecting an account (Login +
picking a Page) works before approval; publishing does not.

Requires META_APP_ID / META_APP_SECRET (server-only env vars). Also
requires the connected Facebook user to be an admin of a Facebook Page,
and for Instagram, that Page must have a linked Instagram professional
(Business/Creator) account — personal IG accounts can't be used at all.
"""

import os

import httpx

META_OAUTH_DIALOG_URL = "https://www.facebook.com/v21.0/dialog/oauth"
META_GRAPH_BASE = "https://graph.facebook.com/v21.0"

# pages_show_list + pages_read_engagement: list the Pages this user
# manages. pages_manage_posts: publish to a Page (Facebook posting).
# instagram_basic + instagram_content_publish: read/publish to the IG
# Business account linked to that Page. business_management: sometimes
# required by Meta for Page/IG asset access depending on app mode.
META_SCOPES = (
    "pages_show_list,pages_read_engagement,pages_manage_posts,"
    "instagram_basic,instagram_content_publish,business_management"
)


def get_backend_url() -> str:
    url = os.getenv("BACKEND_URL")
    if not url:
        raise ValueError(
            "BACKEND_URL environment variable not set — required to build the "
            "Meta OAuth redirect URI (must exactly match a URI registered in "
            "the Meta Developer app's Facebook Login product settings)."
        )
    return url.rstrip("/")


def get_frontend_url() -> str:
    url = os.getenv("FRONTEND_URL")
    if not url:
        raise ValueError("FRONTEND_URL environment variable not set")
    return url.rstrip("/")


def get_redirect_uri() -> str:
    return f"{get_backend_url()}/api/oauth/meta/callback"


def _get_app_id() -> str:
    app_id = os.getenv("META_APP_ID")
    if not app_id:
        raise ValueError("META_APP_ID environment variable not set")
    return app_id


def _get_app_secret() -> str:
    app_secret = os.getenv("META_APP_SECRET")
    if not app_secret:
        raise ValueError("META_APP_SECRET environment variable not set")
    return app_secret


def build_authorize_url(state: str) -> str:
    """Meta's OAuth dialog doesn't use PKCE (confidential server-side app
    flow instead) — state alone guards against CSRF, checked at the
    callback same as X's flow."""
    from urllib.parse import urlencode

    params = {
        "client_id": _get_app_id(),
        "redirect_uri": get_redirect_uri(),
        "state": state,
        "scope": META_SCOPES,
        "response_type": "code",
    }
    return f"{META_OAUTH_DIALOG_URL}?{urlencode(params)}"


async def exchange_code_for_user_token(code: str) -> dict:
    """Step 1 of Meta's flow: authorization code -> short-lived user
    access token."""
    params = {
        "client_id": _get_app_id(),
        "client_secret": _get_app_secret(),
        "redirect_uri": get_redirect_uri(),
        "code": code,
    }
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{META_GRAPH_BASE}/oauth/access_token", params=params)
    response.raise_for_status()
    return response.json()


async def exchange_for_long_lived_token(short_lived_token: str) -> dict:
    """Step 2: short-lived (~1-2hr) user token -> long-lived (~60 day)
    user token. Long-lived Page tokens (derived from this) don't expire
    on their own as long as the user token stays valid, but need
    reconnecting roughly every 60 days if the user token itself lapses."""
    params = {
        "grant_type": "fb_exchange_token",
        "client_id": _get_app_id(),
        "client_secret": _get_app_secret(),
        "fb_exchange_token": short_lived_token,
    }
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{META_GRAPH_BASE}/oauth/access_token", params=params)
    response.raise_for_status()
    return response.json()


async def get_managed_pages(user_access_token: str) -> list[dict]:
    """Lists the Facebook Pages this user manages, each with its own
    long-lived Page access token (Meta issues these alongside the user
    token) and, if present, connected Instagram Business account id.
    WVF has one real Page, so the caller picks (or auto-selects if only
    one) rather than this module guessing."""
    params = {
        "access_token": user_access_token,
        "fields": "id,name,access_token,instagram_business_account",
    }
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{META_GRAPH_BASE}/me/accounts", params=params)
    response.raise_for_status()
    return response.json().get("data", [])


async def publish_facebook_post(page_id: str, page_access_token: str, message: str) -> dict:
    """Publishes a text post to a Facebook Page's feed. Requires
    pages_manage_posts, which is gated behind Meta App Review (see module
    docstring) — will 403 with a permission error until that's approved."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{META_GRAPH_BASE}/{page_id}/feed",
            data={"message": message, "access_token": page_access_token},
        )
    response.raise_for_status()
    return response.json()


async def publish_instagram_post(
    ig_business_account_id: str, page_access_token: str, image_url: str, caption: str
) -> dict:
    """Publishes an image post to an Instagram Business account, linked
    via its parent Facebook Page. Instagram's Content Publishing API is
    two calls: create a media container, then publish it. image_url must
    be a public URL Meta's servers can fetch — this app doesn't host
    generated images (see CLAUDE.md: image prompts are text-only, no
    image files generated/stored), so this is here for when/if that
    changes, not callable from any UI yet. Requires
    instagram_content_publish, gated behind Meta App Review."""
    async with httpx.AsyncClient() as client:
        container = await client.post(
            f"{META_GRAPH_BASE}/{ig_business_account_id}/media",
            data={"image_url": image_url, "caption": caption, "access_token": page_access_token},
        )
        container.raise_for_status()
        creation_id = container.json()["id"]

        publish = await client.post(
            f"{META_GRAPH_BASE}/{ig_business_account_id}/media_publish",
            data={"creation_id": creation_id, "access_token": page_access_token},
        )
    publish.raise_for_status()
    return publish.json()
