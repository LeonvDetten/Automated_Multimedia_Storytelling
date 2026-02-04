"""Story series API endpoints for phase 1."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.repositories.series_repository import list_series
from app.schemas.series import StorySeriesRead

router = APIRouter(prefix="/series", tags=["series"])


@router.get("", response_model=list[StorySeriesRead])
def get_series_endpoint(db: Session = Depends(get_db)) -> list[StorySeriesRead]:
    """Return all available story series."""

    return list_series(db)
