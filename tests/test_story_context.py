"""Unit tests for story context helpers."""

from app.storygen.story_context import estimate_target_words


def test_estimate_target_words_defaults_to_minimum() -> None:
    """Token budgets below threshold should clamp to 120 words."""

    assert estimate_target_words(50) == 120


def test_estimate_target_words_uses_token_budget() -> None:
    """Token budget should scale to word target using 0.75 factor."""

    assert estimate_target_words(800) == 600
    assert estimate_target_words(None) == 600
