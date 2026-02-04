"""Server-rendered web routes for phase 1."""

from fastapi import APIRouter, BackgroundTasks, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.repositories.episode_repository import get_episode, list_recent_episodes
from app.repositories.job_repository import get_job
from app.repositories.series_repository import list_series
from app.repositories.theme_repository import list_themes
from app.repositories.character_repository import list_characters
from app.schemas.episode import EpisodeCreate
from app.services.episode_service import create_episode_and_job

router = APIRouter(tags=["web"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
def index(request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    """Render the main input form with catalog data and recent episodes."""

    context = {
        "request": request,
        "themes": list_themes(db),
        "characters": list_characters(db),
        "series": list_series(db),
        "recent_episodes": list_recent_episodes(db),
    }
    return templates.TemplateResponse("index.html", context)


@router.post("/web/episodes/create", response_class=HTMLResponse)
def create_episode_from_form(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    user_prompt: str = Form(...),
    theme_id: int = Form(...),
    series_id: int | None = Form(None),
    continuation_from_episode_id: str = Form(""),
    character_ids: list[int] = Form(default=[]),
    target_duration_sec: int = Form(15),
    title: str = Form(""),
) -> HTMLResponse:
    """Handle form submission and return a polling job-status partial."""

    continuation_id = int(continuation_from_episode_id) if continuation_from_episode_id else None
    payload = EpisodeCreate(
        user_prompt=user_prompt,
        theme_id=theme_id,
        series_id=series_id,
        continuation_from_episode_id=continuation_id,
        character_ids=character_ids,
        target_duration_sec=target_duration_sec,
        title=title or None,
    )

    try:
        episode_id, job_id = create_episode_and_job(db, payload, background_tasks)
    except HTTPException as exc:
        context = {"request": request, "error_message": exc.detail}
        return templates.TemplateResponse("_job_status.html", context, status_code=exc.status_code)

    job = get_job(db, job_id)
    context = {"request": request, "job": job, "episode_id": episode_id}
    return templates.TemplateResponse("_job_status.html", context)


@router.get("/web/jobs/{job_id}/status", response_class=HTMLResponse)
def get_job_status_partial(job_id: int, request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    """Render a partial snippet with current job state for HTMX polling."""

    job = get_job(db, job_id)
    if not job:
        context = {"request": request, "error_message": "Job not found"}
        return templates.TemplateResponse("_job_status.html", context, status_code=404)

    context = {"request": request, "job": job, "episode_id": job.episode_id}
    return templates.TemplateResponse("_job_status.html", context)


@router.get("/web/episodes/{episode_id}", response_class=HTMLResponse)
def episode_detail(episode_id: int, request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    """Render the detail page for one episode record."""

    episode = get_episode(db, episode_id)
    if not episode:
        raise HTTPException(status_code=404, detail="Episode not found")

    context = {"request": request, "episode": episode}
    return templates.TemplateResponse("episode_detail.html", context)
