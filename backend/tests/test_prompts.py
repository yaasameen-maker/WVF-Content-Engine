"""
Unit tests for prompt construction logic (app/services/prompts.py).

Unlike test_api_e2e.py, these don't go through the FastAPI app or mock the
Anthropic client — they test the actual prompt strings built for Claude,
since bugs here (e.g. contradictory instructions) would otherwise only
surface by reading real generated output.
"""

from app.schemas import EventInput
from app.services.prompts import (
    SOCIAL_POST_PLATFORM_VARIANTS,
    build_social_post_prompt,
    list_variants,
    resolve_variant,
)

SAMPLE_EVENT = EventInput(
    title="Cybersecurity for Small Business",
    date="August 25, 2026",
    speaker="City Bar Justice Center",
    registration_link="https://example.org/register",
    audience="NYC women entrepreneurs",
    description="Learn how to protect your business from cyberattacks.",
)


def test_social_post_platform_variants_are_listed():
    variants = list_variants("social_post")
    for platform in SOCIAL_POST_PLATFORM_VARIANTS:
        assert platform in variants, f"{platform} missing from social_post variant list"
    # Tone variants should still be present alongside platform variants.
    assert "standard" in variants
    assert "listicle" in variants
    assert "quote_style" in variants


def test_facebook_variant_does_not_contradict_emoji_guidance():
    """Regression test: brand_voice.py's shared TONE_GUIDELINES used to
    unconditionally say "use emojis sparingly", which contradicted the
    facebook variant's own instruction to use emoji heavily/structurally
    (matching WVF's real observed Facebook posts). Both the shared
    guidance and the per-variant instructions must agree."""
    prompt = build_social_post_prompt(SAMPLE_EVENT, variant="facebook")
    assert "emojis sparingly" not in prompt
    assert "✔" in prompt  # the real observed WVF Facebook checklist marker


def test_instagram_and_linkedin_variants_also_avoid_sparingly_contradiction():
    for platform in ("instagram", "linkedin"):
        prompt = build_social_post_prompt(SAMPLE_EVENT, variant=platform)
        assert "emojis sparingly" not in prompt, f"{platform} prompt contradicts its own guidance"


def test_tone_variants_still_default_to_sparing_emoji_use():
    """Tone variants (no platform context) should keep the sparing-use
    default — only platform variants override it with their own density."""
    for tone in ("standard", "listicle", "quote_style"):
        prompt = build_social_post_prompt(SAMPLE_EVENT, variant=tone)
        assert "emojis sparingly" in prompt


def test_platform_variants_include_event_details():
    for platform in SOCIAL_POST_PLATFORM_VARIANTS:
        prompt = build_social_post_prompt(SAMPLE_EVENT, variant=platform)
        assert SAMPLE_EVENT.title in prompt
        assert SAMPLE_EVENT.registration_link in prompt


def test_unknown_social_post_variant_raises():
    import pytest

    with pytest.raises(KeyError):
        build_social_post_prompt(SAMPLE_EVENT, variant="not_a_real_variant")


def test_random_variant_selection_never_picks_a_platform_variant():
    """Regression test: platform (instagram/linkedin/facebook) is a
    deliberate staff choice, not a random-rotation axis. "generate_new"
    and "avoid_recent" must never silently land on a platform variant —
    only explicit selection should. Run many times since this is
    random.choice-backed; a single pass could pass by chance if the
    exclusion logic were broken in a way that just reduced probability."""
    platform_set = set(SOCIAL_POST_PLATFORM_VARIANTS)

    generate_new_results = {resolve_variant("social_post", "generate_new") for _ in range(200)}
    assert not (generate_new_results & platform_set), (
        f"generate_new picked platform variant(s): {generate_new_results & platform_set}"
    )

    avoid_recent_results = {
        resolve_variant("social_post", "avoid_recent", recent_variants=["standard"])
        for _ in range(200)
    }
    assert not (avoid_recent_results & platform_set), (
        f"avoid_recent picked platform variant(s): {avoid_recent_results & platform_set}"
    )


def test_explicit_platform_selection_still_works_despite_random_pool_exclusion():
    for platform in SOCIAL_POST_PLATFORM_VARIANTS:
        assert resolve_variant("social_post", platform) == platform
