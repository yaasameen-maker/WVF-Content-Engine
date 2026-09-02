"""
Tests for X OAuth connect flow and manual-click publish
(app/routers/social.py, app/services/x_client.py).

Real X API calls (token exchange, tweet posting) are mocked — no real X
credentials are used or required. What IS exercised for real: PKCE
state generation/validation, the DB upsert logic for SocialConnection,
token encryption round-tripping through the real Fernet implementation,
and the full HTTP/routing layer via FastAPI's TestClient.
"""

import json

import pytest
from cryptography.fernet import Fernet

from app.models import ContentItem, ContentStatus, ContentType, OAuthPkceState, SocialConnection, SocialPlatform
from app.services import x_client
from tests.conftest import SAMPLE_EVENT


@pytest.fixture(autouse=True)
def x_env(monkeypatch):
    """Required env vars for every test in this file — a real (test-only)
    Fernet key, and placeholder X app credentials (never sent anywhere
    real, since the actual API calls are mocked)."""
    monkeypatch.setenv("TOKEN_ENCRYPTION_KEY", Fernet.generate_key().decode())
    monkeypatch.setenv("X_CLIENT_ID", "test-client-id")
    monkeypatch.setenv("X_CLIENT_SECRET", "test-client-secret")
    monkeypatch.setenv("BACKEND_URL", "https://wvf-content-engine-production.up.railway.app")
    monkeypatch.setenv("FRONTEND_URL", "https://wvf-content-engine-two.vercel.app")


def test_start_x_oauth_redirects_to_x_with_pkce_params(client, db_session_factory):
    resp = client.get("/api/oauth/x/start", follow_redirects=False)
    assert resp.status_code in (302, 307)
    location = resp.headers["location"]
    assert location.startswith("https://twitter.com/i/oauth2/authorize")
    assert "code_challenge=" in location
    assert "code_challenge_method=S256" in location
    assert "state=" in location
    assert "client_id=test-client-id" in location

    # A PKCE state row should now exist, ready for the callback to consume.
    db = db_session_factory()
    rows = db.query(OAuthPkceState).all()
    assert len(rows) == 1
    assert rows[0].platform == SocialPlatform.X
    db.close()


def test_x_oauth_callback_rejects_unknown_state(client):
    resp = client.get("/api/oauth/x/callback?code=abc&state=not_a_real_state", follow_redirects=False)
    assert resp.status_code in (302, 307)
    assert "x_connect=error" in resp.headers["location"]
    assert "invalid_state" in resp.headers["location"]


def test_x_oauth_callback_surfaces_user_declined_error(client):
    resp = client.get(
        "/api/oauth/x/callback?error=access_denied&state=whatever", follow_redirects=False
    )
    assert resp.status_code in (302, 307)
    assert "x_connect=error" in resp.headers["location"]
    assert "access_denied" in resp.headers["location"]


def test_x_oauth_callback_completes_connection_on_success(client, db_session_factory, monkeypatch):
    # Simulate a real /start call first, to get a real, valid state/verifier pair.
    start_resp = client.get("/api/oauth/x/start", follow_redirects=False)
    location = start_resp.headers["location"]
    from urllib.parse import urlparse, parse_qs

    state = parse_qs(urlparse(location).query)["state"][0]

    async def fake_exchange(code, code_verifier):
        assert code == "real-auth-code"
        return {
            "access_token": "fake-access-token",
            "refresh_token": "fake-refresh-token",
            "expires_in": 7200,
            "scope": "tweet.read users.read tweet.write offline.access",
        }

    async def fake_get_user(access_token):
        assert access_token == "fake-access-token"
        return {"id": "1234567890", "username": "WomensVFund"}

    monkeypatch.setattr(x_client, "exchange_code_for_tokens", fake_exchange)
    monkeypatch.setattr(x_client, "get_authenticated_user", fake_get_user)

    resp = client.get(
        f"/api/oauth/x/callback?code=real-auth-code&state={state}", follow_redirects=False
    )
    assert resp.status_code in (302, 307)
    assert "x_connect=success" in resp.headers["location"]

    db = db_session_factory()
    connection = db.query(SocialConnection).filter(SocialConnection.platform == SocialPlatform.X).first()
    assert connection is not None
    assert connection.username == "WomensVFund"
    assert connection.platform_account_id == "1234567890"
    # Tokens must be encrypted, not stored as plaintext.
    assert connection.access_token_encrypted != "fake-access-token"
    assert connection.refresh_token_encrypted != "fake-refresh-token"

    # The PKCE state row must be consumed (deleted) after use.
    assert db.query(OAuthPkceState).count() == 0
    db.close()


def test_x_oauth_callback_state_is_single_use(client, monkeypatch):
    start_resp = client.get("/api/oauth/x/start", follow_redirects=False)
    from urllib.parse import urlparse, parse_qs

    state = parse_qs(urlparse(start_resp.headers["location"]).query)["state"][0]

    async def fake_exchange(code, code_verifier):
        return {"access_token": "tok", "expires_in": 7200, "scope": "tweet.write"}

    async def fake_get_user(access_token):
        return {"id": "1", "username": "WomensVFund"}

    monkeypatch.setattr(x_client, "exchange_code_for_tokens", fake_exchange)
    monkeypatch.setattr(x_client, "get_authenticated_user", fake_get_user)

    first = client.get(f"/api/oauth/x/callback?code=abc&state={state}", follow_redirects=False)
    assert "x_connect=success" in first.headers["location"]

    second = client.get(f"/api/oauth/x/callback?code=abc&state={state}", follow_redirects=False)
    assert "x_connect=error" in second.headers["location"]
    assert "invalid_state" in second.headers["location"]


def test_x_status_reports_not_connected_by_default(client):
    resp = client.get("/api/social/x/status")
    assert resp.status_code == 200
    assert resp.json() == {"connected": False, "username": None}


def test_x_status_reports_connected_after_connecting(client, db_session_factory):
    db = db_session_factory()
    from app.services.token_encryption import encrypt_token

    db.add(
        SocialConnection(
            platform=SocialPlatform.X,
            platform_account_id="1",
            username="WomensVFund",
            access_token_encrypted=encrypt_token("tok"),
        )
    )
    db.commit()
    db.close()

    resp = client.get("/api/social/x/status")
    assert resp.status_code == 200
    assert resp.json() == {"connected": True, "username": "WomensVFund"}


def test_disconnect_x_removes_the_connection(client, db_session_factory):
    db = db_session_factory()
    from app.services.token_encryption import encrypt_token

    db.add(
        SocialConnection(
            platform=SocialPlatform.X,
            platform_account_id="1",
            username="WomensVFund",
            access_token_encrypted=encrypt_token("tok"),
        )
    )
    db.commit()
    db.close()

    resp = client.delete("/api/social/x/connection")
    assert resp.status_code == 200
    assert resp.json() == {"disconnected": True}

    assert client.get("/api/social/x/status").json()["connected"] is False


def test_disconnect_x_404s_when_nothing_connected(client):
    resp = client.delete("/api/social/x/connection")
    assert resp.status_code == 404


def _seed_connected_social_post(db_session_factory):
    """Creates a connected X account and one draft social_post ContentItem,
    returns (event_id, content_item_id)."""
    from app.models import Event
    from app.services.token_encryption import encrypt_token

    db = db_session_factory()
    db.add(
        SocialConnection(
            platform=SocialPlatform.X,
            platform_account_id="1",
            username="WomensVFund",
            access_token_encrypted=encrypt_token("valid-access-token"),
        )
    )
    event = Event(**SAMPLE_EVENT)
    db.add(event)
    db.flush()
    item = ContentItem(
        event_id=event.id,
        content_type=ContentType.SOCIAL_POST,
        body=json.dumps({"caption": "Join us for Money & Credit!", "hashtags": ["#WVF"]}),
    )
    db.add(item)
    db.commit()
    ids = (event.id, item.id)
    db.close()
    return ids


def test_post_to_x_publishes_and_records_success(client, db_session_factory, monkeypatch):
    _, content_item_id = _seed_connected_social_post(db_session_factory)

    async def fake_post_tweet(access_token, text):
        assert access_token == "valid-access-token"
        assert text == "Join us for Money & Credit!"
        return {"data": {"id": "999888777", "text": text}}

    monkeypatch.setattr(x_client, "post_tweet", fake_post_tweet)

    resp = client.post("/api/social/x/post", json={"content_item_id": content_item_id})
    assert resp.status_code == 200, resp.text
    assert resp.json() == {"external_post_id": "999888777", "status": "success"}

    db = db_session_factory()
    item = db.query(ContentItem).filter(ContentItem.id == content_item_id).first()
    assert item.status == ContentStatus.PUBLISHED
    db.close()


def test_post_to_x_without_connection_returns_409(client, db_session_factory):
    from app.models import Event

    db = db_session_factory()
    event = Event(**SAMPLE_EVENT)
    db.add(event)
    db.flush()
    item = ContentItem(
        event_id=event.id,
        content_type=ContentType.SOCIAL_POST,
        body=json.dumps({"caption": "test", "hashtags": []}),
    )
    db.add(item)
    db.commit()
    content_item_id = item.id
    db.close()

    resp = client.post("/api/social/x/post", json={"content_item_id": content_item_id})
    assert resp.status_code == 409


def test_post_to_x_404s_for_missing_content_item(client, db_session_factory):
    _seed_connected_social_post(db_session_factory)
    resp = client.post("/api/social/x/post", json={"content_item_id": 999999})
    assert resp.status_code == 404


def test_post_to_x_records_failure_on_api_error(client, db_session_factory, monkeypatch):
    _, content_item_id = _seed_connected_social_post(db_session_factory)

    async def failing_post_tweet(access_token, text):
        raise RuntimeError("X API returned 403")

    monkeypatch.setattr(x_client, "post_tweet", failing_post_tweet)

    resp = client.post("/api/social/x/post", json={"content_item_id": content_item_id})
    assert resp.status_code == 502

    db = db_session_factory()
    from app.models import SocialPost

    posts = db.query(SocialPost).filter(SocialPost.content_item_id == content_item_id).all()
    assert len(posts) == 1
    assert posts[0].status == "failed"
    # The content item's status should NOT have moved to published.
    item = db.query(ContentItem).filter(ContentItem.id == content_item_id).first()
    assert item.status == ContentStatus.DRAFT
    db.close()


def test_token_encryption_round_trips(x_env):
    from app.services.token_encryption import decrypt_token, encrypt_token

    encrypted = encrypt_token("a-real-looking-secret-token")
    assert encrypted != "a-real-looking-secret-token"
    assert decrypt_token(encrypted) == "a-real-looking-secret-token"


# ---------------------------------------------------------------------
# Scheduled auto-posting (POST /api/social/x/run-scheduled-posts) — the
# one deliberate exception to manual-click-only, see social.py's module
# docstring. Approval is a hard gate: these tests specifically cover that
# an approved+due item posts but a draft+due item never does, even with
# an identical scheduled_date/time.
# ---------------------------------------------------------------------

import datetime as dt


@pytest.fixture(autouse=True)
def scheduler_secret_env(monkeypatch):
    monkeypatch.setenv("SCHEDULER_SECRET", "test-scheduler-secret")


def _seed_scheduled_social_post(
    db_session_factory,
    *,
    status,
    scheduled_date,
    scheduled_time=None,
    connected=True,
):
    """Seeds one social_post ContentItem with the given status/schedule,
    and a connected X account unless connected=False. Returns
    content_item_id."""
    from app.models import Event
    from app.services.token_encryption import encrypt_token

    db = db_session_factory()
    if connected:
        db.add(
            SocialConnection(
                platform=SocialPlatform.X,
                platform_account_id="1",
                username="WomensVFund",
                access_token_encrypted=encrypt_token("valid-access-token"),
            )
        )
    event = Event(**SAMPLE_EVENT)
    db.add(event)
    db.flush()
    item = ContentItem(
        event_id=event.id,
        content_type=ContentType.SOCIAL_POST,
        body=json.dumps({"caption": "Scheduled post caption", "hashtags": ["#WVF"]}),
        status=status,
        scheduled_date=scheduled_date,
        scheduled_time=scheduled_time,
    )
    db.add(item)
    db.commit()
    content_item_id = item.id
    db.close()
    return content_item_id


def test_run_scheduled_posts_rejects_missing_secret(client):
    resp = client.post("/api/social/x/run-scheduled-posts")
    assert resp.status_code == 401


def test_run_scheduled_posts_rejects_wrong_secret(client):
    resp = client.post(
        "/api/social/x/run-scheduled-posts", headers={"X-Scheduler-Secret": "wrong"}
    )
    assert resp.status_code == 401


def test_run_scheduled_posts_503s_when_secret_not_configured(client, monkeypatch):
    monkeypatch.delenv("SCHEDULER_SECRET", raising=False)
    resp = client.post(
        "/api/social/x/run-scheduled-posts", headers={"X-Scheduler-Secret": "anything"}
    )
    assert resp.status_code == 503


def test_run_scheduled_posts_publishes_approved_due_item(client, db_session_factory, monkeypatch):
    yesterday = dt.date.today() - dt.timedelta(days=1)
    content_item_id = _seed_scheduled_social_post(
        db_session_factory, status=ContentStatus.APPROVED, scheduled_date=yesterday
    )

    async def fake_post_tweet(access_token, text):
        return {"data": {"id": "555", "text": text}}

    monkeypatch.setattr(x_client, "post_tweet", fake_post_tweet)

    resp = client.post(
        "/api/social/x/run-scheduled-posts", headers={"X-Scheduler-Secret": "test-scheduler-secret"}
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["checked"] == 1
    assert body["posted"] == [
        {"content_item_id": content_item_id, "status": "success", "external_post_id": "555", "error": None}
    ]

    db = db_session_factory()
    item = db.query(ContentItem).filter(ContentItem.id == content_item_id).first()
    assert item.status == ContentStatus.PUBLISHED
    db.close()


def test_run_scheduled_posts_never_publishes_a_draft(client, db_session_factory, monkeypatch):
    """The hard gate this whole feature depends on: scheduling alone
    (even with a due date) must never be enough to publish — approval
    is required. This is the test that would catch a regression letting
    unapproved content go out under WVF's real account."""
    yesterday = dt.date.today() - dt.timedelta(days=1)
    content_item_id = _seed_scheduled_social_post(
        db_session_factory, status=ContentStatus.DRAFT, scheduled_date=yesterday
    )

    async def fake_post_tweet(access_token, text):
        pytest.fail("Should never be called — item is not approved")

    monkeypatch.setattr(x_client, "post_tweet", fake_post_tweet)

    resp = client.post(
        "/api/social/x/run-scheduled-posts", headers={"X-Scheduler-Secret": "test-scheduler-secret"}
    )
    assert resp.status_code == 200
    assert resp.json() == {"checked": 0, "posted": []}

    db = db_session_factory()
    item = db.query(ContentItem).filter(ContentItem.id == content_item_id).first()
    assert item.status == ContentStatus.DRAFT
    db.close()


def test_run_scheduled_posts_skips_future_date(client, db_session_factory, monkeypatch):
    tomorrow = dt.date.today() + dt.timedelta(days=1)
    content_item_id = _seed_scheduled_social_post(
        db_session_factory, status=ContentStatus.APPROVED, scheduled_date=tomorrow
    )

    async def fake_post_tweet(access_token, text):
        pytest.fail("Should never be called — scheduled_date is in the future")

    monkeypatch.setattr(x_client, "post_tweet", fake_post_tweet)

    resp = client.post(
        "/api/social/x/run-scheduled-posts", headers={"X-Scheduler-Secret": "test-scheduler-secret"}
    )
    assert resp.status_code == 200
    assert resp.json() == {"checked": 0, "posted": []}

    db = db_session_factory()
    item = db.query(ContentItem).filter(ContentItem.id == content_item_id).first()
    assert item.status == ContentStatus.APPROVED
    db.close()


def test_run_scheduled_posts_respects_time_today(client, db_session_factory, monkeypatch):
    """Same-day items with a scheduled_time in the future should not
    post yet — only date-past-due or time-already-passed items are due."""
    today = dt.date.today()
    now = dt.datetime.now()
    # Push the "future" time forward by whatever's left until midnight,
    # capped well short of it — a fixed +2h offset can cross into the
    # next calendar day (e.g. a run at 11pm), and _is_due only compares
    # hour:minute with no date awareness, so a wrapped-around time reads
    # as "already passed" instead of "future". Halving the remaining time
    # to midnight guarantees this stays same-day regardless of when the
    # suite runs.
    minutes_until_midnight = (24 * 60) - (now.hour * 60 + now.minute)
    future_time = (now + dt.timedelta(minutes=max(minutes_until_midnight // 2, 1))).strftime("%I:%M %p")
    content_item_id = _seed_scheduled_social_post(
        db_session_factory, status=ContentStatus.APPROVED, scheduled_date=today, scheduled_time=future_time
    )

    async def fake_post_tweet(access_token, text):
        pytest.fail("Should never be called — scheduled_time hasn't arrived yet")

    monkeypatch.setattr(x_client, "post_tweet", fake_post_tweet)

    resp = client.post(
        "/api/social/x/run-scheduled-posts", headers={"X-Scheduler-Secret": "test-scheduler-secret"}
    )
    assert resp.status_code == 200
    # checked counts SQL-level candidates (scheduled_date <= today, which
    # includes today regardless of time) — the time-of-day filter happens
    # in Python afterward, so posted must be empty even though checked isn't.
    assert resp.json() == {"checked": 1, "posted": []}

    db = db_session_factory()
    item = db.query(ContentItem).filter(ContentItem.id == content_item_id).first()
    assert item.status == ContentStatus.APPROVED
    db.close()


def test_run_scheduled_posts_publishes_when_time_today_has_passed(client, db_session_factory, monkeypatch):
    today = dt.date.today()
    past_time = (dt.datetime.now() - dt.timedelta(minutes=5)).strftime("%I:%M %p")
    content_item_id = _seed_scheduled_social_post(
        db_session_factory, status=ContentStatus.APPROVED, scheduled_date=today, scheduled_time=past_time
    )

    async def fake_post_tweet(access_token, text):
        return {"data": {"id": "777", "text": text}}

    monkeypatch.setattr(x_client, "post_tweet", fake_post_tweet)

    resp = client.post(
        "/api/social/x/run-scheduled-posts", headers={"X-Scheduler-Secret": "test-scheduler-secret"}
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["posted"][0]["status"] == "success"

    db = db_session_factory()
    item = db.query(ContentItem).filter(ContentItem.id == content_item_id).first()
    assert item.status == ContentStatus.PUBLISHED
    db.close()


def test_run_scheduled_posts_no_connection_is_a_noop_not_an_error(client, db_session_factory):
    yesterday = dt.date.today() - dt.timedelta(days=1)
    _seed_scheduled_social_post(
        db_session_factory, status=ContentStatus.APPROVED, scheduled_date=yesterday, connected=False
    )

    resp = client.post(
        "/api/social/x/run-scheduled-posts", headers={"X-Scheduler-Secret": "test-scheduler-secret"}
    )
    assert resp.status_code == 200
    assert resp.json() == {"checked": 0, "posted": []}
