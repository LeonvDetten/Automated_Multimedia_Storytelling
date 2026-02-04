"""Episode API endpoints for phase 1."""

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.repositories.episode_repository import get_episode
from app.schemas.episode import EpisodeCreate, EpisodeCreateResponse, EpisodeRead
from app.services.episode_service import create_episode_and_job

router = APIRouter(prefix="/episodes", tags=["episodes"])


@router.post("", response_model=EpisodeCreateResponse, status_code=201)
def create_episode_endpoint(
    payload: EpisodeCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> EpisodeCreateResponse:
    """Create an episode and enqueue a background stub job."""

    episode_id, job_id = create_episode_and_job(db, payload, background_tasks)
    return EpisodeCreateResponse(episode_id=episode_id, job_id=job_id)


@router.get("/{episode_id}", response_model=EpisodeRead)
def get_episode_endpoint(episode_id: int, db: Session = Depends(get_db)) -> EpisodeRead:
    """Return one episode by id."""

    episode = get_episode(db, episode_id)
    if not episode:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Episode not found")
    return episode
