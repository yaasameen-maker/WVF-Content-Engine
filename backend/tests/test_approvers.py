"""
Tests for the approver passcode gate (POST /content/{id}/approve) and
the self-service "forgot passcode" flow (app/routers/approvers.py).

Real email sending is mocked — no real SMTP credentials are used or
required.
"""

import bcrypt
import pytest

from app.models import Approver, PasscodeResetToken
from app.services import email_sender
from tests.conftest import SAMPLE_EVENT


def _seed_approver(db_session_factory, name="Nancy", passcode="TEST1234", email="nancy@example.org"):
    db = db_session_factory()
    db.add(
        Approver(
            name=name,
            email=email,
            passcode_hash=bcrypt.hashpw(passcode.encode(), bcrypt.gensalt()).decode(),
        )
    )
    db.commit()
    approver = db.query(Approver).filter(Approver.name == name).first()
    approver_id = approver.id
    db.close()
    return approver_id, name, passcode, email


def test_forgot_passcode_sends_email_for_known_approver_with_email(client, db_session_factory, monkeypatch):
    approver_id, name, _, email = _seed_approver(db_session_factory)

    sent = {}

    def fake_send(to_email, approver_name, reset_url):
        sent["to_email"] = to_email
        sent["approver_name"] = approver_name
        sent["reset_url"] = reset_url

    monkeypatch.setattr(email_sender, "send_passcode_reset_email", fake_send)
    monkeypatch.setenv("FRONTEND_URL", "https://wvf-content-engine-two.vercel.app")

    resp = client.post("/api/approvers/forgot-passcode", json={"approver_name": name})
    assert resp.status_code == 200
    assert resp.json() == {"ok": True}

    assert sent["to_email"] == email
    assert sent["approver_name"] == name
    assert f"approver={approver_id}" in sent["reset_url"]
    assert "token=" in sent["reset_url"]

    db = db_session_factory()
    tokens = db.query(PasscodeResetToken).filter(PasscodeResetToken.approver_id == approver_id).all()
    assert len(tokens) == 1
    assert tokens[0].used_at is None
    db.close()


def test_forgot_passcode_is_a_noop_for_unknown_approver_but_still_200s(client, monkeypatch):
    called = {"count": 0}

    def fake_send(*args, **kwargs):
        called["count"] += 1

    monkeypatch.setattr(email_sender, "send_passcode_reset_email", fake_send)

    resp = client.post("/api/approvers/forgot-passcode", json={"approver_name": "Nobody"})
    assert resp.status_code == 200
    assert resp.json() == {"ok": True}
    assert called["count"] == 0


def test_forgot_passcode_is_a_noop_when_approver_has_no_email(client, db_session_factory, monkeypatch):
    approver_id, name, _, _ = _seed_approver(db_session_factory, email=None)

    called = {"count": 0}

    def fake_send(*args, **kwargs):
        called["count"] += 1

    monkeypatch.setattr(email_sender, "send_passcode_reset_email", fake_send)

    resp = client.post("/api/approvers/forgot-passcode", json={"approver_name": name})
    assert resp.status_code == 200
    assert called["count"] == 0


def test_reset_passcode_full_flow_then_new_passcode_works_for_approve(client, db_session_factory, monkeypatch):
    approver_id, name, old_passcode, email = _seed_approver(db_session_factory)

    captured = {}

    def fake_send(to_email, approver_name, reset_url):
        captured["reset_url"] = reset_url

    monkeypatch.setattr(email_sender, "send_passcode_reset_email", fake_send)
    monkeypatch.setenv("FRONTEND_URL", "https://wvf-content-engine-two.vercel.app")

    client.post("/api/approvers/forgot-passcode", json={"approver_name": name})
    reset_url = captured["reset_url"]
    token = reset_url.split("token=")[1].split("&")[0]

    new_passcode = "NEWCODE1"
    resp = client.post(
        "/api/approvers/reset-passcode",
        json={"approver_id": approver_id, "token": token, "new_passcode": new_passcode},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json() == {"ok": True}

    # Old passcode should no longer work for a real approve call.
    client.post("/api/generate", json=SAMPLE_EVENT)
    events = client.get("/api/events").json()
    content_id = events[0]["content_items"][0]["id"]

    old_resp = client.post(
        f"/api/content/{content_id}/approve", json={"approver_name": name, "passcode": old_passcode}
    )
    assert old_resp.status_code == 401

    new_resp = client.post(
        f"/api/content/{content_id}/approve", json={"approver_name": name, "passcode": new_passcode}
    )
    assert new_resp.status_code == 200
    assert new_resp.json()["approved_by_name"] == name


def test_reset_passcode_token_is_single_use(client, db_session_factory, monkeypatch):
    approver_id, name, _, _ = _seed_approver(db_session_factory)

    captured = {}

    def fake_send(to_email, approver_name, reset_url):
        captured["reset_url"] = reset_url

    monkeypatch.setattr(email_sender, "send_passcode_reset_email", fake_send)
    monkeypatch.setenv("FRONTEND_URL", "https://wvf-content-engine-two.vercel.app")

    client.post("/api/approvers/forgot-passcode", json={"approver_name": name})
    token = captured["reset_url"].split("token=")[1].split("&")[0]

    first = client.post(
        "/api/approvers/reset-passcode",
        json={"approver_id": approver_id, "token": token, "new_passcode": "FIRSTNEW"},
    )
    assert first.status_code == 200

    second = client.post(
        "/api/approvers/reset-passcode",
        json={"approver_id": approver_id, "token": token, "new_passcode": "SECONDNEW"},
    )
    assert second.status_code == 400


def test_reset_passcode_rejects_wrong_token(client, db_session_factory, monkeypatch):
    approver_id, name, _, _ = _seed_approver(db_session_factory)

    monkeypatch.setattr(email_sender, "send_passcode_reset_email", lambda *a, **k: None)
    monkeypatch.setenv("FRONTEND_URL", "https://wvf-content-engine-two.vercel.app")

    client.post("/api/approvers/forgot-passcode", json={"approver_name": name})

    resp = client.post(
        "/api/approvers/reset-passcode",
        json={"approver_id": approver_id, "token": "totally-wrong-token", "new_passcode": "NEWCODE1"},
    )
    assert resp.status_code == 400


def test_reset_passcode_rejects_too_short_passcode(client, db_session_factory, monkeypatch):
    approver_id, name, _, _ = _seed_approver(db_session_factory)

    captured = {}
    monkeypatch.setattr(
        email_sender, "send_passcode_reset_email", lambda to_email, approver_name, reset_url: captured.update(url=reset_url)
    )
    monkeypatch.setenv("FRONTEND_URL", "https://wvf-content-engine-two.vercel.app")

    client.post("/api/approvers/forgot-passcode", json={"approver_name": name})
    token = captured["url"].split("token=")[1].split("&")[0]

    resp = client.post(
        "/api/approvers/reset-passcode",
        json={"approver_id": approver_id, "token": token, "new_passcode": "abc"},
    )
    assert resp.status_code == 422
