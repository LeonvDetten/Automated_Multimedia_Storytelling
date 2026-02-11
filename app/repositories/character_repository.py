"""Character repository helpers."""

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from app.models.character import Character
from app.schemas.character import CharacterCreate


def list_characters(db: Session) -> list[Character]:
    """Return active characters sorted by name."""

    statement: Select[tuple[Character]] = select(Character).where(Character.active.is_(True)).order_by(Character.name.asc())
    return list(db.scalars(statement).all())


def list_all_characters(db: Session) -> list[Character]:
    """Return all characters sorted by name."""

    statement: Select[tuple[Character]] = select(Character).order_by(Character.name.asc())
    return list(db.scalars(statement).all())


def create_character(db: Session, payload: CharacterCreate) -> Character:
    """Insert and return a new character row."""

    character = Character(**payload.model_dump())
    db.add(character)
    db.commit()
    db.refresh(character)
    return character


def get_character(db: Session, character_id: int) -> Character | None:
    """Return a single character by id."""

    return db.get(Character, character_id)


def update_character(
    db: Session,
    character: Character,
    *,
    name: str,
    speech_style: str,
    description: str,
    traits_json: dict,
    active: bool,
) -> Character:
    """Update an existing character."""

    character.name = name
    character.speech_style = speech_style
    character.description = description
    character.traits_json = traits_json
    character.active = active
    db.commit()
    db.refresh(character)
    return character


def delete_character(db: Session, character: Character) -> None:
    """Delete a character row."""

    db.delete(character)
    db.commit()


def get_characters_by_ids(db: Session, character_ids: list[int]) -> list[Character]:
    """Return all characters that match the given ids."""

    if not character_ids:
        return []
    statement: Select[tuple[Character]] = select(Character).where(Character.id.in_(character_ids))
    return list(db.scalars(statement).all())
