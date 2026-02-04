"""Theme API endpoints for phase 1."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.repositories.theme_repository import list_themes
from app.schemas.theme import ThemeRead

router = APIRouter(prefix="/themes", tags=["themes"])


@router.get("", response_model=list[ThemeRead])
def get_themes(db: Session = Depends(get_db)) -> list[ThemeRead]:
    """Return all active story themes."""

    return list_themes(db)
