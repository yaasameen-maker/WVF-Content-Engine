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
    SOCIAL_POST_SERIES_HINTS,
    SOCIAL_POST_TONE_HINTS,
    build_social_post_prompt,
    list_social_post_series,
    list_social_post_tones,
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


def test_social_post_series_hint_is_injected_into_prompt():
    prompt = build_social_post_prompt(SAMPLE_EVENT, series="financial_literacy_friday")
    assert SOCIAL_POST_SERIES_HINTS["financial_literacy_friday"] in prompt


def test_social_post_tone_hint_is_injected_into_prompt():
    prompt = build_social_post_prompt(SAMPLE_EVENT, tone="urgent")
    assert SOCIAL_POST_TONE_HINTS["urgent"] in prompt


def test_social_post_series_and_tone_can_combine():
    prompt = build_social_post_prompt(SAMPLE_EVENT, series="grant_opportunity", tone="celebratory")
    assert SOCIAL_POST_SERIES_HINTS["grant_opportunity"] in prompt
    assert SOCIAL_POST_TONE_HINTS["celebratory"] in prompt


def test_unknown_series_and_tone_are_silently_ignored():
    """Optional steering, not a required/validated selection — an unknown
    key (e.g. a stale frontend build sending an old key) should not raise
    or corrupt the prompt, just produce the same prompt as if unset."""
    prompt_with_bogus = build_social_post_prompt(SAMPLE_EVENT, series="not_a_real_series", tone="not_a_real_tone")
    prompt_unset = build_social_post_prompt(SAMPLE_EVENT)
    assert prompt_with_bogus == prompt_unset


def test_list_social_post_series_returns_all_labeled_keys():
    series = list_social_post_series()
    assert set(series.keys()) == set(SOCIAL_POST_SERIES_HINTS.keys())
    assert all(isinstance(label, str) and label for label in series.values())


def test_list_social_post_tones_returns_all_labeled_keys():
    tones = list_social_post_tones()
    assert set(tones.keys()) == set(SOCIAL_POST_TONE_HINTS.keys())
    assert all(isinstance(label, str) and label for label in tones.values())


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


def test_x_and_tiktok_variants_do_not_claim_real_wvf_observation():
    """X and TikTok, unlike instagram/linkedin/facebook, have no real WVF
    sample posts behind them yet — their own structural instructions
    (SOCIAL_POST_VARIANTS[platform]["instructions"]) must not claim
    "real"/"observed" WVF style the way the other three correctly do,
    since that would misrepresent generic platform conventions as
    verified brand voice."""
    from app.services.prompts import SOCIAL_POST_VARIANTS

    for platform in ("x", "tiktok"):
        instructions = SOCIAL_POST_VARIANTS[platform]["instructions"].lower()
        assert "real" not in instructions and "observed" not in instructions, (
            f"{platform} instructions should not claim real/observed WVF style"
        )
        assert "not yet grounded" in instructions or "general" in instructions, (
            f"{platform} instructions should be explicit about being generic, not WVF-specific"
        )


def test_x_and_tiktok_variants_include_event_details():
    for platform in ("x", "tiktok"):
        prompt = build_social_post_prompt(SAMPLE_EVENT, variant=platform)
        assert SAMPLE_EVENT.title in prompt
        assert SAMPLE_EVENT.registration_link in prompt


def test_missing_registration_link_is_not_interpolated_as_none():
    """registration_link is optional (Aug 2026) — staff can add the real
    link later by editing generated copy rather than being blocked from
    generating without one. The prompt must never contain a literal
    "None"/blank from naive interpolation, and must explicitly tell
    Claude not to invent a placeholder link."""
    event_no_link = SAMPLE_EVENT.model_copy(update={"registration_link": None})
    prompt = build_social_post_prompt(event_no_link)
    assert "- Registration: None" not in prompt
    assert "do not invent a link" in prompt


def test_present_registration_link_still_appears_normally():
    prompt = build_social_post_prompt(SAMPLE_EVENT)
    assert f"- Registration: {SAMPLE_EVENT.registration_link}" in prompt
