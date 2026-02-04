"""Story series repository helpers."""

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from app.models.story_series import StorySeries


def list_series(db: Session) -> list[StorySeries]:
    """Return all story series ordered by creation date descending."""

    statement: Select[tuple[StorySeries]] = select(StorySeries).order_by(StorySeries.created_at.desc())
    return list(db.scalars(statement).all())


def get_series(db: Session, series_id: int) -> StorySeries | None:
    """Return one series by id."""

    return db.get(StorySeries, series_id)


def get_default_series(db: Session) -> StorySeries | None:
    """Return the oldest available series as fallback."""

    statement: Select[tuple[StorySeries]] = select(StorySeries).order_by(StorySeries.id.asc()).limit(1)
    return db.scalar(statement)
