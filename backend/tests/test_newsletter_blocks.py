"""
E2E tests for the /api/newsletter-blocks endpoint. Anthropic calls are
mocked (see conftest.py fake_generate_newsletter_blocks) so these exercise
the real HTTP/DB path without hitting Claude.
"""

from tests.conftest import SAMPLE_EVENT


def test_list_block_types_returns_all_six(client):
    resp = client.get("/api/newsletter-blocks/types")
    assert resp.status_code == 200
    assert set(resp.json()) == {
        "feature_article", "events_list", "grant_flyer",
        "tips_cta", "member_spotlight", "boilerplate",
    }


def test_generate_blocks_requires_event_id_or_event(client):
    resp = client.post("/api/newsletter-blocks", json={"block_types": ["boilerplate"]})
    assert resp.status_code == 400
    assert "event_id or event" in resp.json()["detail"]


def test_generate_blocks_rejects_unknown_block_type(client):
    resp = client.post(
        "/api/newsletter-blocks",
        json={"event": SAMPLE_EVENT, "block_types": ["not_a_real_block"]},
    )
    assert resp.status_code == 400
    assert "Unknown block type" in resp.json()["detail"]


def test_generate_single_block_with_fresh_event(client):
    resp = client.post(
        "/api/newsletter-blocks",
        json={"event": SAMPLE_EVENT, "block_types": ["boilerplate"]},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert len(body) == 1
    assert body[0]["block_type"] == "boilerplate"
    assert set(body[0]["body"].keys()) == {"about_blurb", "phone", "email", "website"}


def test_generate_all_six_blocks_persists_each_as_own_content_item(client):
    resp = client.post(
        "/api/newsletter-blocks",
        json={"event": SAMPLE_EVENT},  # block_types defaults to all six
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert len(body) == 6
    block_types = {item["block_type"] for item in body}
    assert block_types == {
        "feature_article", "events_list", "grant_flyer",
        "tips_cta", "member_spotlight", "boilerplate",
    }
    # each has a distinct persisted id
    assert len({item["id"] for item in body}) == 6


def test_generate_blocks_using_existing_event_id(client):
    # First, create a real event via /api/generate (which also seeds content_items).
    gen_resp = client.post("/api/generate", json=SAMPLE_EVENT)
    assert gen_resp.status_code == 200
    event_id = client.get("/api/events").json()[0]["id"]

    resp = client.post(
        "/api/newsletter-blocks",
        json={"event_id": event_id, "block_types": ["events_list"]},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert len(body) == 1
    assert body[0]["block_type"] == "events_list"

    # Confirm it's tied to the real event via the events endpoint.
    event_detail = client.get(f"/api/events/{event_id}").json()
    newsletter_block_items = [
        ci for ci in event_detail["content_items"] if ci["content_type"] == "newsletter_block"
    ]
    assert len(newsletter_block_items) == 1
    assert newsletter_block_items[0]["block_type"] == "events_list"


def test_generate_blocks_with_nonexistent_event_id_404s(client):
    resp = client.post(
        "/api/newsletter-blocks",
        json={"event_id": 999999, "block_types": ["boilerplate"]},
    )
    assert resp.status_code == 404


def test_generate_member_spotlight_with_nonexistent_key_maker_404s(client):
    resp = client.post(
        "/api/newsletter-blocks",
        json={
            "event": SAMPLE_EVENT,
            "block_types": ["member_spotlight"],
            "key_maker_id": 999999,
        },
    )
    assert resp.status_code == 404


def test_newsletter_block_items_have_draft_status(client):
    resp = client.post(
        "/api/newsletter-blocks",
        json={"event": SAMPLE_EVENT, "block_types": ["tips_cta"]},
    )
    content_id = resp.json()[0]["id"]

    fetched = client.get(f"/api/content/{content_id}")
    assert fetched.status_code == 200
    assert fetched.json()["status"] == "draft"
    assert fetched.json()["content_type"] == "newsletter_block"
