"""Character repository helpers."""

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from app.models.character import Character
from app.schemas.character import CharacterCreate


def list_characters(db: Session) -> list[Character]:
    """Return active characters sorted by name."""

    statement: Select[tuple[Character]] = select(Character).where(Character.active.is_(True)).order_by(Character.name.asc())
    return list(db.scalars(statement).all())


def create_character(db: Session, payload: CharacterCreate) -> Character:
    """Insert and return a new character row."""

    character = Character(**payload.model_dump())
    db.add(character)
    db.commit()
    db.refresh(character)
    return character


def get_characters_by_ids(db: Session, character_ids: list[int]) -> list[Character]:
    """Return all characters that match the given ids."""

    if not character_ids:
        return []
    statement: Select[tuple[Character]] = select(Character).where(Character.id.in_(character_ids))
    return list(db.scalars(statement).all())
