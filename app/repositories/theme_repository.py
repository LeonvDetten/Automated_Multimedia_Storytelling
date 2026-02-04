"""Theme repository helpers."""

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from app.models.theme import Theme


def list_themes(db: Session) -> list[Theme]:
    """Return all active themes sorted by label."""

    statement: Select[tuple[Theme]] = select(Theme).where(Theme.active.is_(True)).order_by(Theme.label.asc())
    return list(db.scalars(statement).all())


def get_theme(db: Session, theme_id: int) -> Theme | None:
    """Return a single theme by id when present."""

    return db.get(Theme, theme_id)
