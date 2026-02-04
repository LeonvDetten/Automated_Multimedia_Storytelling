"""Character API endpoints for phase 1."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.repositories.character_repository import create_character, list_characters
from app.schemas.character import CharacterCreate, CharacterRead

router = APIRouter(prefix="/characters", tags=["characters"])


@router.get("", response_model=list[CharacterRead])
def get_characters(db: Session = Depends(get_db)) -> list[CharacterRead]:
    """Return all active characters for selection in the UI."""

    return list_characters(db)


@router.post("", response_model=CharacterRead, status_code=201)
def create_character_endpoint(payload: CharacterCreate, db: Session = Depends(get_db)) -> CharacterRead:
    """Create a new reusable character definition."""

    return create_character(db, payload)
