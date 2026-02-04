"""Episode repository helpers."""

from sqlalchemy import Select, desc, func, select
from sqlalchemy.orm import Session

from app.models.episode import Episode, EpisodeCharacter


def get_episode(db: Session, episode_id: int) -> Episode | None:
    """Return one episode by id."""

    return db.get(Episode, episode_id)


def list_recent_episodes(db: Session, limit: int = 10) -> list[Episode]:
    """Return recent episodes for quick UI selection."""

    statement: Select[tuple[Episode]] = select(Episode).order_by(desc(Episode.created_at)).limit(limit)
    return list(db.scalars(statement).all())


def next_episode_number(db: Session, series_id: int) -> int:
    """Return the next episode number within a series."""

    statement = select(func.max(Episode.episode_number)).where(Episode.series_id == series_id)
    current_max = db.scalar(statement)
    return (current_max or 0) + 1


def create_episode(
    db: Session,
    *,
    series_id: int,
    title: str,
    user_prompt: str,
    theme_id: int,
    continuation_from_episode_id: int | None,
    character_ids: list[int],
    target_duration_sec: int,
) -> Episode:
    """Create an episode and its character links in one transaction."""

    episode = Episode(
        series_id=series_id,
        episode_number=next_episode_number(db, series_id),
        title=title,
        user_prompt=user_prompt,
        theme_id=theme_id,
        continuation_from_episode_id=continuation_from_episode_id,
        target_duration_sec=target_duration_sec,
        status="draft",
    )
    db.add(episode)
    db.flush()

    for character_id in character_ids:
        db.add(EpisodeCharacter(episode_id=episode.id, character_id=character_id, role="support"))

    db.commit()
    db.refresh(episode)
    return episode
