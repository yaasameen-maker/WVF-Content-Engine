"""
Pexels stock photo search — free, no-approval-wait stock photography
backing the photo + text composer's "Stock photos" tab (see
frontend/components/PhotoTextComposer.tsx). This backend only ever
proxies search requests so the Pexels API key stays server-side; it
never stores or re-hosts the photos themselves — the frontend loads
image URLs straight from Pexels' own CDN, same as it already does for
R2-hosted photo-library images.

Free tier: 200 requests/hour, 20,000/month — more than enough at WVF's
volume (a handful of staff searching occasionally, not bulk/automated
calls). Pexels' license permits commercial use with no attribution
required, though crediting the photographer is still good practice.

Proposed scope addition, not yet approved by WVF — offered as an
alternative to AI-generated backdrops (see the still-unbuilt
image_generation.py placeholder in .env.example), since real stock
photography needs no new AI-generation cost, moderation surface, or
reversal of PROJECT_CONTEXT.md's "no image files generated" line —
these are pre-existing licensed photos, not generated ones.
"""

import os

import httpx

PEXELS_SEARCH_URL = "https://api.pexels.com/v1/search"
DEFAULT_PER_PAGE = 15


class PexelsNotConfigured(Exception):
    """Raised when PEXELS_API_KEY isn't set — callers (the router)
    should surface this as a 503, matching SCHEDULER_SECRET's pattern
    in app/routers/social.py, rather than a generic 500."""


def search_photos(query: str, per_page: int = DEFAULT_PER_PAGE) -> list[dict]:
    """Searches Pexels for `query`, returning a list of
    {id, photographer, alt, src_url, thumbnail_url} — just the fields
    the composer's photo grid needs, not Pexels' full response shape.
    src_url is Pexels' "large" size (good enough for the composer's
    1080x1080 canvas without over-fetching the "original" size)."""
    api_key = os.getenv("PEXELS_API_KEY")
    if not api_key:
        raise PexelsNotConfigured(
            "PEXELS_API_KEY environment variable not set — required for stock photo search. "
            "Generate a free key at pexels.com/api."
        )

    response = httpx.get(
        PEXELS_SEARCH_URL,
        params={"query": query, "per_page": per_page},
        headers={"Authorization": api_key},
        timeout=10.0,
    )
    response.raise_for_status()
    data = response.json()

    return [
        {
            "id": photo["id"],
            "photographer": photo["photographer"],
            "alt": photo.get("alt") or query,
            "src_url": photo["src"]["large"],
            "thumbnail_url": photo["src"]["tiny"],
        }
        for photo in data.get("photos", [])
    ]
