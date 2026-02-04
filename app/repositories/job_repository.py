"""Job repository helpers."""

from sqlalchemy.orm import Session

from app.models.job import Job


def create_job(db: Session, episode_id: int, job_type: str = "phase1_stub") -> Job:
    """Create and persist a new queued job for an episode."""

    job = Job(episode_id=episode_id, type=job_type, status="queued", progress_pct=0, step="queued")
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def get_job(db: Session, job_id: int) -> Job | None:
    """Return one job by id."""

    return db.get(Job, job_id)


def update_job_state(db: Session, job_id: int, *, status: str, progress_pct: int, step: str, error_message: str | None = None) -> Job | None:
    """Update the current state values for a job."""

    job = get_job(db, job_id)
    if not job:
        return None

    job.status = status
    job.progress_pct = progress_pct
    job.step = step
    job.error_message = error_message
    db.commit()
    db.refresh(job)
    return job
