"""Build a structured context for story generation (Phase 2).

This module is the single place where you gather *all* inputs needed to
compose a good prompt: form data, database lookups, and optional continuation
details. Keep this file small and explicit so prompt-building stays simple.
"""

from dataclasses import dataclass
from typing import Any

from sqlalchemy.orm import Session

from app.models.episode import Episode
from app.models.story_series import StorySeries
from app.models.theme import Theme
from app.repositories.character_repository import get_characters_by_ids
from app.repositories.episode_repository import get_episode, next_episode_number
from app.repositories.series_repository import get_series
from app.repositories.theme_repository import get_default_theme, get_theme
from app.schemas.episode import EpisodeCreate


@dataclass
class CharacterProfile:
    """Lightweight character payload for prompt building."""

    id: int
    name: str
    speech_style: str
    description: str
    traits: dict[str, Any]


@dataclass
class ContinuationContext:
    """Optional context about a previous episode."""

    episode_id: int
    title: str
    summary: str | None
    script_text: str | None
    user_prompt: str


@dataclass
class StoryContext:
    """All structured inputs needed for Phase 2 story generation."""

    user_prompt: str
    theme_label: str | None
    theme_description: str | None
    is_standalone: bool
    series_title: str | None
    episode_number: int | None
    continuation: ContinuationContext | None
    characters: list[CharacterProfile]
    max_output_tokens: int
    target_words: int


def estimate_target_words(max_output_tokens: int | None) -> int:
    """Estimate a word target based on the max token budget."""

    token_budget = max_output_tokens or 800
    return max(120, round(token_budget * 0.75))


def build_story_context(db: Session, payload: EpisodeCreate) -> StoryContext:
    """Build a StoryContext from the incoming form payload and DB lookups.

    Important form inputs (from EpisodeCreate):
    - payload.user_prompt
    - payload.theme_id (optional)
    - payload.series_id (optional)
    - payload.is_standalone (bool)
    - payload.character_ids (list[int])
    - payload.continuation_from_episode_id (optional)
    - payload.target_duration_sec (available if you want time-based prompts)
    """

    theme: Theme | None
    if payload.theme_id is None:
        theme = get_default_theme(db)
    else:
        theme = get_theme(db, payload.theme_id)

    series: StorySeries | None = None
    episode_number: int | None = None
    if not payload.is_standalone and payload.series_id:
        series = get_series(db, payload.series_id)
        if series:
            episode_number = next_episode_number(db, series.id)

    continuation: ContinuationContext | None = None
    if payload.continuation_from_episode_id:
        previous: Episode | None = get_episode(db, payload.continuation_from_episode_id)
        if previous:
            continuation = ContinuationContext(
                episode_id=previous.id,
                title=previous.title,
                summary=previous.summary,
                script_text=previous.script_text,
                user_prompt=previous.user_prompt,
            )

    characters = [
        CharacterProfile(
            id=character.id,
            name=character.name,
            speech_style=character.speech_style,
            description=character.description,
            traits=character.traits_json,
        )
        for character in get_characters_by_ids(db, payload.character_ids)
    ]

    return StoryContext(
        user_prompt=payload.user_prompt,
        theme_label=theme.label if theme else None,
        theme_description=theme.description if theme else None,
        is_standalone=payload.is_standalone,
        series_title=series.title if series else None,
        episode_number=episode_number,
        continuation=continuation,
        characters=characters,
        max_output_tokens=payload.max_output_tokens or 800,
        target_words=estimate_target_words(payload.max_output_tokens),
    )
