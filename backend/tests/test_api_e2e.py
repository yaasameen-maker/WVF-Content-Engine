"""
End-to-end tests against the real FastAPI app + a real (isolated) SQLite DB.

Anthropic calls are mocked (see conftest.py) so the suite runs without an API
key and without network access, but every HTTP layer, DB write, and response
schema is exercised for real. This is meant to catch endpoint contract
breaks (renamed fields, wrong status codes, broken FK relationships) before
they reach a PR.
"""

from tests.conftest import SAMPLE_EVENT


def test_health_check_reports_db_connected(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "healthy"
    assert body["database"] == "connected"


def test_root_health_check(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert resp.json()["status"] == "healthy"


def test_generate_returns_all_content_types(client):
    resp = client.post("/api/generate", json=SAMPLE_EVENT)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert set(body.keys()) == {"social_post", "hashtags", "newsletter", "flyer", "calendar"}

    assert set(body["social_post"].keys()) == {
        "caption", "hashtags", "suggested_image_prompt", "cta",
    }
    assert set(body["hashtags"].keys()) == {
        "primary_hashtags", "topic_hashtags", "rationale",
    }
    assert set(body["newsletter"].keys()) == {
        "subject_line", "preview_text", "body", "cta_text", "cta_link",
    }
    assert set(body["flyer"].keys()) == {
        "headline", "subheadline", "body", "cta", "footer_details",
    }
    assert set(body["calendar"].keys()) == {"weeks", "entries"}
    assert body["calendar"]["entries"]
    assert set(body["calendar"]["entries"][0].keys()) == {
        "day_label", "platform", "post_idea", "hashtags", "cta",
    }


def test_generate_rejects_incomplete_event(client):
    incomplete = {k: v for k, v in SAMPLE_EVENT.items() if k != "title"}
    resp = client.post("/api/generate", json=incomplete)
    assert resp.status_code == 422


def test_generate_persists_event_and_all_content_items(client):
    resp = client.post("/api/generate", json=SAMPLE_EVENT)
    assert resp.status_code == 200

    events_resp = client.get("/api/events")
    assert events_resp.status_code == 200
    events = events_resp.json()
    assert len(events) == 1

    event = events[0]
    for field in (
        "id", "title", "date", "speaker", "registration_link",
        "audience", "description", "created_at", "updated_at", "content_items",
    ):
        assert field in event, f"missing field '{field}' on event response"

    assert event["title"] == SAMPLE_EVENT["title"]
    assert len(event["content_items"]) == 5

    content_types = {item["content_type"] for item in event["content_items"]}
    assert content_types == {"social_post", "hashtags", "newsletter", "flyer", "calendar"}
    assert all(item["status"] == "draft" for item in event["content_items"])


def test_get_single_event_returns_404_when_missing(client):
    resp = client.get("/api/events/999999")
    assert resp.status_code == 404


def test_get_single_event_matches_list_response(client):
    client.post("/api/generate", json=SAMPLE_EVENT)
    events = client.get("/api/events").json()
    event_id = events[0]["id"]

    resp = client.get(f"/api/events/{event_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == event_id
    assert len(resp.json()["content_items"]) == 5


def test_get_content_item_returns_404_when_missing(client):
    resp = client.get("/api/content/999999")
    assert resp.status_code == 404


def test_content_item_full_lifecycle_edit_then_approve(client):
    client.post("/api/generate", json=SAMPLE_EVENT)
    events = client.get("/api/events").json()
    content_item = events[0]["content_items"][0]
    content_id = content_item["id"]
    assert content_item["status"] == "draft"

    edited_body = dict(content_item["body"])
    edited_body["caption" if "caption" in edited_body else next(iter(edited_body))] = "STAFF EDITED"
    patch_resp = client.patch(f"/api/content/{content_id}", json={"body": edited_body})
    assert patch_resp.status_code == 200, patch_resp.text
    assert patch_resp.json()["status"] == "draft"

    approve_resp = client.post(f"/api/content/{content_id}/approve")
    assert approve_resp.status_code == 200
    assert approve_resp.json()["status"] == "approved"

    fetched = client.get(f"/api/content/{content_id}").json()
    assert fetched["status"] == "approved"
    assert fetched["body"] == edited_body


def test_patch_rejects_invalid_status_value(client):
    client.post("/api/generate", json=SAMPLE_EVENT)
    content_id = client.get("/api/events").json()[0]["content_items"][0]["id"]

    resp = client.patch(f"/api/content/{content_id}", json={"status": "not_a_real_status"})
    assert resp.status_code == 422


def test_patch_content_item_404_when_missing(client):
    resp = client.patch("/api/content/999999", json={"status": "approved"})
    assert resp.status_code == 404


def test_approve_content_item_404_when_missing(client):
    resp = client.post("/api/content/999999/approve")
    assert resp.status_code == 404


def test_events_list_ordered_newest_first(client):
    first = dict(SAMPLE_EVENT, title="First Event")
    second = dict(SAMPLE_EVENT, title="Second Event")

    client.post("/api/generate", json=first)
    client.post("/api/generate", json=second)

    events = client.get("/api/events").json()
    assert len(events) == 2
    assert events[0]["title"] == "Second Event"
    assert events[1]["title"] == "First Event"
