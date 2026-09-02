"""
Shared "is this content item due / stale" logic for scheduled auto-
posting — used by both app/routers/social.py's run_scheduled_x_posts
(to decide what to actually post) and the ContentItemResponse
serializers in routers/content.py and routers/generate.py (to compute
is_stale for display, e.g. a warning banner on the review/calendar
pages). Kept in one place so the two can never define "due"/"stale"
differently.
"""

from datetime import datetime, timedelta

from app.models import ContentItem

# How long past its scheduled moment an approved item is still allowed
# to auto-post once approved (e.g. approved a day late after a slow
# review). Past this, it's considered stale — never auto-posted, but
# left as status=approved so a human can still manually "Post to X" if
# they actually want to send it late. See ContentItemResponse.is_stale.
STALE_AFTER = timedelta(hours=72)


def parse_scheduled_time(raw: str) -> tuple[int, int] | None:
    """Best-effort parse of scheduled_time's free-text value (e.g.
    "2:30 PM", "14:30") into (hour, minute). Returns None if it can't be
    parsed — callers treat that as "no specific time," i.e. due as soon
    as the date arrives, rather than blocking a post forever on a
    malformed string a staff member typed."""
    raw = raw.strip()
    for fmt in ("%I:%M %p", "%H:%M", "%I:%M%p"):
        try:
            parsed = datetime.strptime(raw, fmt)
            return parsed.hour, parsed.minute
        except ValueError:
            continue
    return None


def scheduled_moment(item: ContentItem) -> datetime | None:
    """Combines scheduled_date + scheduled_time into a real datetime, at
    midnight if no time is set/parseable — the earliest moment this item
    could be considered due. Returns None if there's no scheduled_date at
    all (never a candidate for auto-posting)."""
    if item.scheduled_date is None:
        return None
    parsed_time = parse_scheduled_time(item.scheduled_time) if item.scheduled_time else None
    hour, minute = parsed_time or (0, 0)
    return datetime.combine(item.scheduled_date, datetime.min.time()).replace(hour=hour, minute=minute)


def is_due(item: ContentItem, now: datetime) -> bool:
    moment = scheduled_moment(item)
    if moment is None:
        return False
    return moment <= now


def is_stale(item: ContentItem, now: datetime | None = None) -> bool:
    """True once an item's scheduled moment has passed by more than
    STALE_AFTER — excluded from auto-posting even though it's still
    technically "due" by is_due's definition. Always False once the
    item has actually been published (a stale-but-published item isn't
    a stale problem anymore) or if it was never scheduled at all."""
    if item.status == "published" or (hasattr(item.status, "value") and item.status.value == "published"):
        return False
    moment = scheduled_moment(item)
    if moment is None:
        return False
    now = now or datetime.now()
    return now - moment > STALE_AFTER
