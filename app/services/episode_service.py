"""Episode orchestration service for phase 1."""

from fastapi import BackgroundTasks, HTTPException, status
from sqlalchemy.orm import Session

from app.repositories.character_repository import get_characters_by_ids
from app.repositories.episode_repository import create_episode, get_episode
from app.repositories.job_repository import create_job
from app.repositories.series_repository import get_default_series, get_series
from app.repositories.theme_repository import get_theme
from app.schemas.episode import EpisodeCreate
from app.services.job_service import run_job_stub


def _resolve_series_id(db: Session, series_id: int | None) -> int:
    """Resolve a requested series id or fallback to the default series."""

    if series_id is not None:
        if not get_series(db, series_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Series not found")
        return series_id

    default_series = get_default_series(db)
    if not default_series:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No story series available")
    return default_series.id


def create_episode_and_job(db: Session, payload: EpisodeCreate, background_tasks: BackgroundTasks) -> tuple[int, int]:
    """Validate payload, create episode + job, and schedule a stub background task."""

    theme = get_theme(db, payload.theme_id)
    if not theme or not theme.active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Theme not found")

    if payload.continuation_from_episode_id is not None:
        continuation_episode = get_episode(db, payload.continuation_from_episode_id)
        if not continuation_episode:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Continuation episode not found")

    characters = get_characters_by_ids(db, payload.character_ids)
    if len(characters) != len(set(payload.character_ids)):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="One or more characters were not found")

    resolved_series_id = _resolve_series_id(db, payload.series_id)
    title = payload.title or "Generated Episode"

    episode = create_episode(
        db,
        series_id=resolved_series_id,
        title=title,
        user_prompt=payload.user_prompt,
        theme_id=payload.theme_id,
        continuation_from_episode_id=payload.continuation_from_episode_id,
        character_ids=payload.character_ids,
        target_duration_sec=payload.target_duration_sec,
    )

    job = create_job(db, episode.id)
    background_tasks.add_task(run_job_stub, job.id)

    return episode.id, job.id
