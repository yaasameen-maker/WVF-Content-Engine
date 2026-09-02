"""
End-to-end tests against the real FastAPI app + a real (isolated) SQLite DB.

Anthropic calls are mocked (see conftest.py) so the suite runs without an API
key and without network access, but every HTTP layer, DB write, and response
schema is exercised for real. This is meant to catch endpoint contract
breaks (renamed fields, wrong status codes, broken FK relationships) before
they reach a PR.
"""

from app.models import Approver, KeyMaker
from tests.conftest import SAMPLE_EVENT


def _seed_approver(db_session_factory, name="Nancy", passcode="TEST1234"):
    """Creates a real Approver row with a known (test-only) passcode, for
    tests that need to exercise the passcode-gated /approve endpoint."""
    import bcrypt

    db = db_session_factory()
    db.add(Approver(name=name, passcode_hash=bcrypt.hashpw(passcode.encode(), bcrypt.gensalt()).decode()))
    db.commit()
    db.close()
    return name, passcode


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


def test_generate_succeeds_without_registration_link(client):
    """registration_link is the one optional EventInput field (Aug 2026)
    — staff can generate content before a link exists and add it later
    by editing the generated copy. Unlike test_generate_rejects_incomplete_event
    above (a genuinely required field), omitting this one must succeed."""
    no_link = {k: v for k, v in SAMPLE_EVENT.items() if k != "registration_link"}
    resp = client.post("/api/generate", json=no_link)
    assert resp.status_code == 200, resp.text

    events = client.get("/api/events").json()
    assert events[0]["registration_link"] is None


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


def test_event_and_content_item_timestamps_are_utc_marked(client):
    """created_at/updated_at are stored as naive UTC internally
    (datetime.utcnow() everywhere in the models) — Pydantic serializes a
    naive datetime with NO timezone suffix, which the frontend's
    `new Date(iso)` then silently misreads as local time instead of UTC,
    shifting the displayed timestamp by the browser's UTC offset (the
    real bug a user hit live: a post created "now" showed as created
    hours in the future). Every timestamp in the JSON response must end
    in Z (or a numeric UTC offset) so JS parses it correctly."""
    resp = client.post("/api/generate", json=SAMPLE_EVENT)
    assert resp.status_code == 200

    event = client.get("/api/events").json()[0]
    assert event["created_at"].endswith("Z") or "+00:00" in event["created_at"]
    assert event["updated_at"].endswith("Z") or "+00:00" in event["updated_at"]

    for item in event["content_items"]:
        assert item["created_at"].endswith("Z") or "+00:00" in item["created_at"], item["created_at"]
        assert item["updated_at"].endswith("Z") or "+00:00" in item["updated_at"], item["updated_at"]


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
    assert set(detail.keys()) == {"label", "category", "caption", "hashtags", "truncated"}
    assert detail["category"] == "event_promo"
    assert "Ready to make 2027 your year" in detail["caption"]
    assert "#WomensVentureFund" in detail["hashtags"]
    assert detail["truncated"] is False


def test_instagram_template_detail_handles_empty_hashtags(client):
    # Several real posts (e.g. quote cards) had no hashtags in the source.
    resp = client.get("/api/instagram-templates/tribe_of_women_quote")
    assert resp.status_code == 200
    assert resp.json()["hashtags"] == []


def test_instagram_template_detail_flags_truncated_source(client):
    # legal_help_urgency's source screenshot cut off part of the real
    # caption (see instagram_templates.py) — the API must say so.
    resp = client.get("/api/instagram-templates/legal_help_urgency")
    assert resp.status_code == 200
    assert resp.json()["truncated"] is True


def test_instagram_template_detail_404s_for_unknown_template(client):
    resp = client.get("/api/instagram-templates/not_a_real_template")
    assert resp.status_code == 404
    assert "not_a_real_template" in resp.json()["detail"]


def test_x_templates_endpoint_lists_all_templates(client):
    resp = client.get("/api/x-templates")
    assert resp.status_code == 200
    templates = resp.json()
    assert len(templates) == 6
    assert all(isinstance(label, str) and label for label in templates.values())


def test_x_template_detail_returns_real_post_content(client):
    resp = client.get("/api/x-templates/government_contracting")
    assert resp.status_code == 200
    detail = resp.json()
    assert set(detail.keys()) == {"label", "category", "caption", "hashtags", "truncated"}
    assert detail["category"] == "event_promo"
    assert "MWBE" in detail["caption"]
    assert "#GovernmentContracts" in detail["hashtags"]
    assert detail["truncated"] is False


def test_x_template_detail_flags_truncated_source(client):
    # money_credit_webinar's source screenshot cut off the zoom.us URL
    # (see x_templates.py) — the API must say so, not present it as complete.
    resp = client.get("/api/x-templates/money_credit_webinar")
    assert resp.status_code == 200
    assert resp.json()["truncated"] is True


def test_x_template_detail_404s_for_unknown_template(client):
    resp = client.get("/api/x-templates/not_a_real_template")
    assert resp.status_code == 404
    assert "not_a_real_template" in resp.json()["detail"]


def test_social_post_series_endpoint_lists_all_series(client):
    resp = client.get("/api/social-post-series")
    assert resp.status_code == 200
    series = resp.json()
    assert "financial_literacy_friday" in series
    assert all(isinstance(label, str) and label for label in series.values())


def test_social_post_tones_endpoint_lists_all_tones(client):
    resp = client.get("/api/social-post-tones")
    assert resp.status_code == 200
    tones = resp.json()
    assert "urgent" in tones
    assert all(isinstance(label, str) and label for label in tones.values())


def test_generate_accepts_social_post_series_and_tone_without_error(client):
    payload = {**SAMPLE_EVENT, "social_post_series": "top_3", "social_post_tone": "celebratory"}
    resp = client.post("/api/generate", json=payload)
    assert resp.status_code == 200, resp.text


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


def test_content_item_full_lifecycle_edit_then_approve(client, db_session_factory):
    name, passcode = _seed_approver(db_session_factory)

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

    approve_resp = client.post(
        f"/api/content/{content_id}/approve", json={"approver_name": name, "passcode": passcode}
    )
    assert approve_resp.status_code == 200, approve_resp.text
    assert approve_resp.json()["status"] == "approved"
    assert approve_resp.json()["approved_by_name"] == name

    fetched = client.get(f"/api/content/{content_id}").json()
    assert fetched["status"] == "approved"
    assert fetched["body"] == edited_body


def test_approve_content_item_rejects_wrong_passcode(client, db_session_factory):
    name, _ = _seed_approver(db_session_factory)

    client.post("/api/generate", json=SAMPLE_EVENT)
    events = client.get("/api/events").json()
    content_id = events[0]["content_items"][0]["id"]

    resp = client.post(
        f"/api/content/{content_id}/approve", json={"approver_name": name, "passcode": "wrong-code"}
    )
    assert resp.status_code == 401

    fetched = client.get(f"/api/content/{content_id}").json()
    assert fetched["status"] == "draft"


def test_approve_content_item_rejects_unknown_approver(client, db_session_factory):
    client.post("/api/generate", json=SAMPLE_EVENT)
    events = client.get("/api/events").json()
    content_id = events[0]["content_items"][0]["id"]

    resp = client.post(
        f"/api/content/{content_id}/approve",
        json={"approver_name": "Nobody", "passcode": "anything"},
    )
    assert resp.status_code == 401


def test_patch_rejects_invalid_status_value(client):
    client.post("/api/generate", json=SAMPLE_EVENT)
    content_id = client.get("/api/events").json()[0]["content_items"][0]["id"]

    resp = client.patch(f"/api/content/{content_id}", json={"status": "not_a_real_status"})
    assert resp.status_code == 422


def test_patch_content_item_404_when_missing(client):
    resp = client.patch("/api/content/999999", json={"status": "approved"})
    assert resp.status_code == 404


def test_approve_content_item_404_when_missing(client, db_session_factory):
    name, passcode = _seed_approver(db_session_factory)
    resp = client.post(
        "/api/content/999999/approve", json={"approver_name": name, "passcode": passcode}
    )
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


def test_list_key_makers_returns_public_fields_only(client, db_session_factory):
    db = db_session_factory()
    db.add(
        KeyMaker(
            business_name="LASweetsNY",
            owner_name="Loretta Calderon",
            business_type="Bakery / Catering",
            website="https://lasweetsny.com",
            social_media="Instagram: @lasweetsny",
            testimonial_quote=None,
            video_link=None,
            photo_url=None,
        )
    )
    db.commit()
    db.close()

    resp = client.get("/api/key-makers")
    assert resp.status_code == 200
    key_makers = resp.json()
    assert len(key_makers) == 1

    key_maker = key_makers[0]
    assert set(key_maker.keys()) == {
        "id", "business_name", "owner_name", "business_type", "website",
        "social_media", "testimonial_quote", "video_link", "photo_url",
        "title", "location", "industry", "key_quotes", "story",
    }
    assert key_maker["business_name"] == "LASweetsNY"
    assert key_maker["owner_name"] == "Loretta Calderon"
    # Bio not yet collected — must be null, never fabricated or blank string.
    assert key_maker["testimonial_quote"] is None
    assert key_maker["title"] is None
    assert key_maker["story"] is None
    assert key_maker["key_quotes"] is None
    # KeyMakerPrivate fields (phone/email/address) must never appear here.
    assert "phone" not in key_maker
    assert "email" not in key_maker
    assert "address" not in key_maker


def test_list_key_makers_ordered_alphabetically_by_business_name(client, db_session_factory):
    db = db_session_factory()
    db.add_all(
        [
            KeyMaker(business_name="Zeta Consulting", owner_name="Owner Z"),
            KeyMaker(business_name="Alpha Bakery", owner_name="Owner A"),
        ]
    )
    db.commit()
    db.close()

    resp = client.get("/api/key-makers")
    assert resp.status_code == 200
    names = [k["business_name"] for k in resp.json()]
    assert names == ["Alpha Bakery", "Zeta Consulting"]


def test_get_single_key_maker_returns_matching_record(client, db_session_factory):
    db = db_session_factory()
    key_maker = KeyMaker(business_name="LASweetsNY", owner_name="Loretta Calderon")
    db.add(key_maker)
    db.commit()
    db.refresh(key_maker)
    key_maker_id = key_maker.id
    db.close()

    resp = client.get(f"/api/key-makers/{key_maker_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == key_maker_id
    assert resp.json()["business_name"] == "LASweetsNY"


def test_get_single_key_maker_404s_when_missing(client):
    resp = client.get("/api/key-makers/999999")
    assert resp.status_code == 404


def test_key_maker_with_full_bio_returns_structured_fields(client, db_session_factory):
    import json

    db = db_session_factory()
    key_maker = KeyMaker(
        business_name="LASweetsNY",
        owner_name="Loretta Calderon",
        title="CEO",
        location="Harlem, New York",
        industry="Food / Culinary / Hospitality",
        key_quotes=json.dumps(["Quote one.", "Quote two."]),
        story="A long real narrative bio.",
    )
    db.add(key_maker)
    db.commit()
    db.refresh(key_maker)
    key_maker_id = key_maker.id
    db.close()

    resp = client.get(f"/api/key-makers/{key_maker_id}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["title"] == "CEO"
    assert body["location"] == "Harlem, New York"
    assert body["industry"] == "Food / Culinary / Hospitality"
    # key_quotes round-trips as a real list, not a raw JSON string.
    assert body["key_quotes"] == ["Quote one.", "Quote two."]
    assert body["story"] == "A long real narrative bio."
