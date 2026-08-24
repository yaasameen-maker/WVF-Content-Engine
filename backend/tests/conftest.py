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
    BoilerplateBlock,
    CalendarPostEntry,
    ContentCalendarOutput,
    EventListEntry,
    EventsListBlock,
    FeatureArticleBlock,
    FlyerOutput,
    GeneratedContentResponse,
    GrantEntry,
    GrantFlyerBlock,
    HashtagsOutput,
    HashtagsVariant,
    MemberSpotlightBlock,
    NewsletterOutput,
    SocialPostOutput,
    SocialPostVariant,
    TipsCtaBlock,
)


# 3 distinct fake options, matching SOCIAL_POST_VARIANT_COUNT — real
# generate_social_post_variants()/generate_hashtags_variants() always
# return exactly this many, so the fake mirrors that shape rather than
# collapsing to one, keeping the E2E test honest about the real API
# contract the frontend picker relies on.
FAKE_SOCIAL_POST_VARIANTS = [
    SocialPostVariant(
        structure_variant="standard",
        structure_label="Standard",
        post=SocialPostOutput(
            caption="Join us for Money & Credit! Learn to build a strong financial foundation.",
            hashtags=["#WomensVentureFund", "#CreditEducation"],
            suggested_image_prompt="Navy and sky-blue banner with event title, WVF logo",
            cta="Register Now",
        ),
    ),
    SocialPostVariant(
        structure_variant="listicle",
        structure_label="Listicle",
        post=SocialPostOutput(
            caption="3 things you'll learn at Money & Credit:\n1. Credit basics\n2. Building your score\n3. Avoiding common mistakes",
            hashtags=["#WomensVentureFund", "#CreditEducation"],
            suggested_image_prompt="Navy and sky-blue banner with a numbered list overlay",
            cta="Save Your Spot",
        ),
    ),
    SocialPostVariant(
        structure_variant="quote_style",
        structure_label="Quote-style",
        post=SocialPostOutput(
            caption='"Your credit score shouldn\'t be a mystery." Join WVF for a free webinar on credit fundamentals.',
            hashtags=["#WomensVentureFund", "#CreditEducation"],
            suggested_image_prompt="Navy and sky-blue banner with a pull-quote overlay",
            cta="Register Today",
        ),
    ),
]

FAKE_HASHTAGS_VARIANTS = [
    HashtagsVariant(
        hashtags=HashtagsOutput(
            primary_hashtags=["#WomensVentureFund", "#WVFCDFI"],
            topic_hashtags=["#CreditEducation", "#FinancialLiteracy"],
            rationale="Matches event topic and WVF's core brand hashtags.",
        )
    ),
    HashtagsVariant(
        hashtags=HashtagsOutput(
            primary_hashtags=["#WomensVentureFund", "#WVFCDFI"],
            topic_hashtags=["#CreditScore", "#SmallBusinessNYC"],
            rationale="Alternate topic-specific angle for the same event.",
        )
    ),
    HashtagsVariant(
        hashtags=HashtagsOutput(
            primary_hashtags=["#WomensVentureFund", "#WVFCDFI"],
            topic_hashtags=["#BuildYourCredit", "#WomenInBusiness"],
            rationale="Third alternate angle, pairs with the quote-style caption.",
        )
    ),
]

FAKE_GENERATED_CONTENT = GeneratedContentResponse(
    event_id=1,
    social_post_variants=FAKE_SOCIAL_POST_VARIANTS,
    hashtags_variants=FAKE_HASHTAGS_VARIANTS,
    newsletter=NewsletterOutput(
        subject_line="Money & Credit: Free Webinar This Month",
        preview_text="Build your credit, build your business.",
        body="<p>Join WVF for a free webinar on credit fundamentals.</p>",
        body_plain_text="Join WVF for a free webinar on credit fundamentals.",
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

FAKE_NEWSLETTER_BLOCKS = {
    "feature_article": FeatureArticleBlock(
        headline="Contracting With the Government: An Overview",
        body="If your goal is to do business with the government, this briefing is for you.",
        cta_text="Read More",
    ),
    "events_list": EventsListBlock(
        entries=[
            EventListEntry(
                title="Money & Credit",
                date="2026-08-15",
                time="2:00 PM ET",
                registration_link="https://wvf.org/register",
            )
        ]
    ),
    "grant_flyer": GrantFlyerBlock(
        entries=[
            GrantEntry(
                name="AT&T Small Business Contest",
                amount="$50,000",
                deadline="July 31, 2026",
                eligibility="Small business owners",
            )
        ]
    ),
    "tips_cta": TipsCtaBlock(
        headline="Take Advantage of Our Business Resources",
        pitch="Training, mentorship, and financial resources for every stage of your journey.",
        image_prompt="Navy and sky-blue banner with WVF logo watermark",
    ),
    "member_spotlight": MemberSpotlightBlock(
        headline="From Passion to Performance",
        body="A WVF Key Maker's journey from idea to thriving business.",
        cta_text="Read More",
    ),
    "boilerplate": BoilerplateBlock(
        about_blurb="WVF has served more than 17,000 firms across NYC.",
        phone="(212) 563-0499",
        email="info@wvf-ny.org",
        website="www.womenventurefund.org",
    ),
}

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

    async def fake_generate_all_content(
        event,
        social_post_platform=None,
        newsletter_variant_selection="generate_new",
        recent_newsletter_variants=None,
        keymakers_stage_key=None,
        social_post_series=None,
        social_post_tone=None,
    ):
        return FAKE_GENERATED_CONTENT, keymakers_stage_key or "standard"

    monkeypatch.setattr(
        "app.routers.generate.generate_all_content", fake_generate_all_content
    )

    async def fake_generate_newsletter_blocks(
        event,
        block_types,
        key_maker_business_name=None,
        key_maker_owner_name=None,
        key_maker_business_type=None,
    ):
        return {bt: FAKE_NEWSLETTER_BLOCKS[bt] for bt in block_types}

    monkeypatch.setattr(
        "app.routers.newsletter_blocks.generate_newsletter_blocks",
        fake_generate_newsletter_blocks,
    )

    from fastapi.testclient import TestClient

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
