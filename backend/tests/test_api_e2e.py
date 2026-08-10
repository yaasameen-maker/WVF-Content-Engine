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
        "subject_line", "preview_text", "body", "body_plain_text", "cta_text", "cta_link",
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


def test_keymakers_stages_endpoint_lists_all_stages(client):
    resp = client.get("/api/keymakers-stages")
    assert resp.status_code == 200
    stages = resp.json()
    assert set(stages.keys()) == {
        "current_clients_initial",
        "current_clients_follow_up_1",
        "current_clients_follow_up_2",
        "current_clients_final_follow_up",
        "cold_list_initial",
    }
    # Every value is a non-empty label, for a dropdown.
    assert all(isinstance(label, str) and label for label in stages.values())


def test_generate_with_keymakers_stage_key_persists_it_as_newsletter_variant(client):
    payload = {**SAMPLE_EVENT, "keymakers_stage_key": "current_clients_follow_up_1"}
    resp = client.post("/api/generate", json=payload)
    assert resp.status_code == 200, resp.text

    events = client.get("/api/events").json()
    newsletter_item = next(
        item for item in events[0]["content_items"] if item["content_type"] == "newsletter"
    )
    # The fake generator in conftest.py echoes keymakers_stage_key back as
    # the resolved newsletter variant — mirrors how a real Keymakers
    # generation call should record which stage was used, the same way a
    # normal call records which structural variant was used.
    assert newsletter_item.get("structure_variant") == "current_clients_follow_up_1"


def test_generate_with_invalid_keymakers_stage_key_returns_400(monkeypatch, client):
    # conftest.py's fake generator doesn't validate the stage key (it just
    # echoes it back), so this test exercises the real
    # keymakers_campaign.get_keymakers_stage_context() KeyError path by
    # patching in a generator that raises the way the real one does.
    from app.services.keymakers_campaign import get_keymakers_stage_context

    async def raising_fake_generate_all_content(event, **kwargs):
        if kwargs.get("keymakers_stage_key"):
            get_keymakers_stage_context(kwargs["keymakers_stage_key"])  # raises KeyError
        raise AssertionError("should have raised before reaching here")

    monkeypatch.setattr(
        "app.routers.generate.generate_all_content", raising_fake_generate_all_content
    )

    payload = {**SAMPLE_EVENT, "keymakers_stage_key": "not_a_real_stage"}
    resp = client.post("/api/generate", json=payload)
    assert resp.status_code == 400, resp.text
    assert "not_a_real_stage" in resp.json()["detail"]


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
