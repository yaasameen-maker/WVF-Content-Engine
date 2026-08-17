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
    assert set(body.keys()) == {
        "event_id", "social_post_variants", "hashtags_variants", "newsletter", "flyer", "calendar",
    }
    assert isinstance(body["event_id"], int)

    # 3 options each, matching SOCIAL_POST_VARIANT_COUNT — see conftest.py.
    assert len(body["social_post_variants"]) == 3
    assert len(body["hashtags_variants"]) == 3
    for variant in body["social_post_variants"]:
        assert set(variant.keys()) == {"structure_variant", "structure_label", "post"}
        assert set(variant["post"].keys()) == {
            "caption", "hashtags", "suggested_image_prompt", "cta",
        }
    for variant in body["hashtags_variants"]:
        assert set(variant.keys()) == {"hashtags"}
        assert set(variant["hashtags"].keys()) == {
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


def test_generate_persists_event_and_immediate_content_items(client):
    """social_post/hashtags are NOT persisted at generate time — only
    newsletter/flyer/calendar are (see POST /api/generate docstring and
    POST /api/content/select-social-variant, exercised separately below)."""
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
    assert len(event["content_items"]) == 3

    content_types = {item["content_type"] for item in event["content_items"]}
    assert content_types == {"newsletter", "flyer", "calendar"}
    assert all(item["status"] == "draft" for item in event["content_items"])


def test_select_social_variant_persists_the_picked_pair(client):
    gen_resp = client.post("/api/generate", json=SAMPLE_EVENT)
    generated = gen_resp.json()
    event_id = generated["event_id"]

    picked_social_post = generated["social_post_variants"][1]  # "listicle" in the fake
    picked_hashtags = generated["hashtags_variants"][1]["hashtags"]

    select_resp = client.post(
        "/api/content/select-social-variant",
        json={
            "event_id": event_id,
            "social_post_variant": picked_social_post,
            "hashtags": picked_hashtags,
        },
    )
    assert select_resp.status_code == 200, select_resp.text
    created = select_resp.json()
    assert len(created) == 2
    content_types = {item["content_type"] for item in created}
    assert content_types == {"social_post", "hashtags"}

    social_item = next(item for item in created if item["content_type"] == "social_post")
    assert social_item["structure_variant"] == picked_social_post["structure_variant"]
    assert social_item["body"]["caption"] == picked_social_post["post"]["caption"]

    hashtags_item = next(item for item in created if item["content_type"] == "hashtags")
    assert hashtags_item["body"]["primary_hashtags"] == picked_hashtags["primary_hashtags"]

    # Now the event should carry all 5 content items — the 3 from
    # generate time plus the 2 just persisted by the pick.
    event = client.get(f"/api/events/{event_id}").json()
    assert len(event["content_items"]) == 5
    assert {item["content_type"] for item in event["content_items"]} == {
        "social_post", "hashtags", "newsletter", "flyer", "calendar",
    }


def test_select_social_variant_404s_for_missing_event(client):
    resp = client.post(
        "/api/content/select-social-variant",
        json={
            "event_id": 999999,
            "social_post_variant": {
                "structure_variant": "standard",
                "structure_label": "Standard",
                "post": {
                    "caption": "x",
                    "hashtags": [],
                    "suggested_image_prompt": "x",
                    "cta": "x",
                },
            },
            "hashtags": {"primary_hashtags": [], "topic_hashtags": [], "rationale": "x"},
        },
    )
    assert resp.status_code == 404


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


def test_keymakers_stage_detail_returns_real_reference_copy(client):
    resp = client.get("/api/keymakers-stages/current_clients_follow_up_1")
    assert resp.status_code == 200
    detail = resp.json()
    assert set(detail.keys()) == {
        "label", "audience", "stage", "send_day", "subject_options", "body",
    }
    assert detail["label"] == "Day 4 follow-up — Current WVF Clients"
    assert detail["audience"] == "Current WVF Clients"
    assert detail["send_day"] == 4
    assert "What was your key" in detail["body"]
    # This stage has subject_options in the source data.
    assert detail["subject_options"]
    # send_condition exists in the source dict but isn't part of the
    # response shape (internal staff sequencing guidance, not display copy).
    assert "send_condition" not in detail


def test_keymakers_stage_detail_omits_subject_options_when_absent(client):
    # The "initial" stage has no subject_options in the source data.
    resp = client.get("/api/keymakers-stages/current_clients_initial")
    assert resp.status_code == 200
    assert resp.json()["subject_options"] is None


def test_keymakers_stage_detail_404s_for_unknown_stage(client):
    resp = client.get("/api/keymakers-stages/not_a_real_stage")
    assert resp.status_code == 404
    assert "not_a_real_stage" in resp.json()["detail"]


def test_instagram_templates_endpoint_lists_all_templates(client):
    resp = client.get("/api/instagram-templates")
    assert resp.status_code == 200
    templates = resp.json()
    assert len(templates) == 10
    # Every value is a non-empty label, for a picker UI.
    assert all(isinstance(label, str) and label for label in templates.values())


def test_instagram_template_detail_returns_real_post_content(client):
    resp = client.get("/api/instagram-templates/money_credit_webinar")
    assert resp.status_code == 200
    detail = resp.json()
    assert set(detail.keys()) == {"label", "category", "caption", "hashtags"}
    assert detail["category"] == "event_promo"
    assert "Ready to make 2027 your year" in detail["caption"]
    assert "#WomensVentureFund" in detail["hashtags"]


def test_instagram_template_detail_handles_empty_hashtags(client):
    # Several real posts (e.g. quote cards) had no hashtags in the source.
    resp = client.get("/api/instagram-templates/tribe_of_women_quote")
    assert resp.status_code == 200
    assert resp.json()["hashtags"] == []


def test_instagram_template_detail_404s_for_unknown_template(client):
    resp = client.get("/api/instagram-templates/not_a_real_template")
    assert resp.status_code == 404
    assert "not_a_real_template" in resp.json()["detail"]


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
    # 3 at generate time (newsletter/flyer/calendar) — social_post/hashtags
    # aren't persisted until select-social-variant, see that test above.
    assert len(resp.json()["content_items"]) == 3


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
