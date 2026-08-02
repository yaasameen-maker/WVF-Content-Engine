"""
Shared pytest fixtures for the E2E API test suite.

Uses an isolated file-based SQLite DB per test (not the dev DB), created fresh
from the SQLAlchemy models so schema drift between models and Alembic
migrations doesn't silently pass. Real Anthropic calls are never made -
generate_all_content is monkeypatched to a fixed fake response so the suite
is fast, free, and deterministic while still exercising the real HTTP/DB path.
"""

import os
import sys
import uuid

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.database import Base, get_db
from app.main import app
from app.schemas import (
    CalendarPostEntry,
    ContentCalendarOutput,
    FlyerOutput,
    GeneratedContentResponse,
    HashtagsOutput,
    NewsletterOutput,
    SocialPostOutput,
)


FAKE_GENERATED_CONTENT = GeneratedContentResponse(
    social_post=SocialPostOutput(
        caption="Join us for Money & Credit! Learn to build a strong financial foundation.",
        hashtags=["#WomensVentureFund", "#CreditEducation"],
        suggested_image_prompt="Navy and sky-blue banner with event title, WVF logo",
        cta="Register Now",
    ),
    hashtags=HashtagsOutput(
        primary_hashtags=["#WomensVentureFund", "#WVFCDFI"],
        topic_hashtags=["#CreditEducation", "#FinancialLiteracy"],
        rationale="Matches event topic and WVF's core brand hashtags.",
    ),
    newsletter=NewsletterOutput(
        subject_line="Money & Credit: Free Webinar This Month",
        preview_text="Build your credit, build your business.",
        body="<p>Join WVF for a free webinar on credit fundamentals.</p>",
        cta_text="Register Today",
        cta_link="https://wvf.org/register",
    ),
    flyer=FlyerOutput(
        headline="Money & Credit",
        subheadline="Build Your Financial Foundation",
        body="Free webinar covering credit basics for entrepreneurs.",
        cta="Register Today",
        footer_details="Aug 15, 2026 | Jane Doe | wvf.org/register",
    ),
    calendar=ContentCalendarOutput(
        weeks=2,
        entries=[
            CalendarPostEntry(
                day_label="Week 1, Monday",
                platform="Instagram",
                post_idea="Event announcement",
                hashtags=["#WomensVentureFund"],
                cta="Register Now",
            ),
            CalendarPostEntry(
                day_label="Week 2, Friday",
                platform="LinkedIn",
                post_idea="Reminder post",
                hashtags=["#CreditEducation"],
                cta="Save Your Spot",
            ),
        ],
    ),
)

SAMPLE_EVENT = {
    "title": "Money & Credit",
    "date": "2026-08-15",
    "speaker": "Jane Doe",
    "registration_link": "https://wvf.org/register",
    "audience": "Small business owners",
    "description": "A webinar on credit basics for entrepreneurs.",
}


@pytest.fixture()
def db_session_factory(tmp_path):
    """Fresh SQLite DB file per test, schema created from the live models."""
    db_path = tmp_path / f"test_{uuid.uuid4().hex}.db"
    engine = create_engine(
        f"sqlite:///{db_path}", connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    yield TestingSessionLocal
    engine.dispose()


@pytest.fixture()
def client(db_session_factory, monkeypatch):
    """TestClient wired to the isolated DB, with Claude calls mocked out."""

    def override_get_db():
        db = db_session_factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    async def fake_generate_all_content(event):
        return FAKE_GENERATED_CONTENT

    monkeypatch.setattr(
        "app.routers.generate.generate_all_content", fake_generate_all_content
    )

    from fastapi.testclient import TestClient

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
