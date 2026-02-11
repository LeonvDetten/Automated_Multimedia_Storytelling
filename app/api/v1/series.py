"""Story series API endpoints for phase 1."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.repositories.series_repository import create_series, list_series
from app.schemas.series import StorySeriesCreate, StorySeriesRead

router = APIRouter(prefix="/series", tags=["series"])


@router.get("", response_model=list[StorySeriesRead])
def get_series_endpoint(db: Session = Depends(get_db)) -> list[StorySeriesRead]:
    """Return all available story series."""

    return list_series(db)


@router.post("", response_model=StorySeriesRead, status_code=201)
def create_series_endpoint(payload: StorySeriesCreate, db: Session = Depends(get_db)) -> StorySeriesRead:
    """Create a new story series."""

    return create_series(db, title=payload.title, description=payload.description, language=payload.language)
