"""Server-rendered web routes for phase 1."""

from fastapi import APIRouter, BackgroundTasks, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.episode import Episode
from app.models.story_series import StorySeries
from app.repositories.character_repository import list_characters
from app.repositories.episode_repository import get_episode, list_recent_episodes
from app.repositories.job_repository import get_job
from app.repositories.series_repository import create_series, list_series
from app.repositories.theme_repository import list_themes
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


def _confirm_or_error(confirm_check: str, confirm_text: str) -> str | None:
    """Validate the delete confirmation inputs."""

    if confirm_check.lower() not in {"true", "on", "1", "yes"}:
        return "Please confirm the checkbox before deleting."
    if confirm_text.strip().upper() != "DELETE":
        return "Please type DELETE to confirm."
    return None


@router.get("/delete", response_class=HTMLResponse)
def delete_center(request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    """Render the delete center for episodes, series, and standalone movies."""

    episodes = list(db.scalars(select(Episode).order_by(Episode.created_at.desc())).all())
    series_list = list(db.scalars(select(StorySeries).order_by(StorySeries.created_at.desc())).all())
    standalone = [episode for episode in episodes if episode.series_id is None]

    context = {
        "request": request,
        "episodes": episodes,
        "series": series_list,
        "standalone": standalone,
    }
    return templates.TemplateResponse("delete.html", context)


@router.post("/delete/episode", response_class=HTMLResponse)
def delete_episode_action(
    request: Request,
    db: Session = Depends(get_db),
    episode_id: int = Form(...),
    confirm_check: str = Form(""),
    confirm_text: str = Form(""),
) -> HTMLResponse:
    """Delete a single episode by id after confirmation."""

    error = _confirm_or_error(confirm_check, confirm_text)
    if error:
        return _render_delete_with_message(request, db, error, "error")

    episode = db.get(Episode, episode_id)
    if not episode:
        return _render_delete_with_message(request, db, "Episode not found.", "error")

    db.delete(episode)
    db.commit()
    return _render_delete_with_message(request, db, "Episode deleted.", "success")


@router.post("/delete/standalone", response_class=HTMLResponse)
def delete_standalone_action(
    request: Request,
    db: Session = Depends(get_db),
    episode_id: int = Form(...),
    confirm_check: str = Form(""),
    confirm_text: str = Form(""),
) -> HTMLResponse:
    """Delete a standalone movie episode after confirmation."""

    error = _confirm_or_error(confirm_check, confirm_text)
    if error:
        return _render_delete_with_message(request, db, error, "error")

    episode = db.get(Episode, episode_id)
    if not episode or episode.series_id is not None:
        return _render_delete_with_message(request, db, "Standalone movie not found.", "error")

    db.delete(episode)
    db.commit()
    return _render_delete_with_message(request, db, "Standalone movie deleted.", "success")


@router.post("/delete/series", response_class=HTMLResponse)
def delete_series_action(
    request: Request,
    db: Session = Depends(get_db),
    series_id: int = Form(...),
    confirm_check: str = Form(""),
    confirm_text: str = Form(""),
) -> HTMLResponse:
    """Delete a series and all of its episodes after confirmation."""

    error = _confirm_or_error(confirm_check, confirm_text)
    if error:
        return _render_delete_with_message(request, db, error, "error")

    series = db.get(StorySeries, series_id)
    if not series:
        return _render_delete_with_message(request, db, "Series not found.", "error")

    episodes = list(db.scalars(select(Episode).where(Episode.series_id == series_id)).all())
    for episode in episodes:
        db.delete(episode)

    db.delete(series)
    db.commit()
    return _render_delete_with_message(request, db, "Series and episodes deleted.", "success")


def _render_delete_with_message(request: Request, db: Session, message: str, kind: str) -> HTMLResponse:
    """Re-render the delete page with a feedback message."""

    episodes = list(db.scalars(select(Episode).order_by(Episode.created_at.desc())).all())
    series_list = list(db.scalars(select(StorySeries).order_by(StorySeries.created_at.desc())).all())
    standalone = [episode for episode in episodes if episode.series_id is None]

    context = {
        "request": request,
        "episodes": episodes,
        "series": series_list,
        "standalone": standalone,
        "message": message,
        "message_kind": kind,
    }
    return templates.TemplateResponse("delete.html", context)


@router.post("/web/episodes/create", response_class=HTMLResponse)
def create_episode_from_form(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    user_prompt: str = Form(...),
    theme_id: str = Form(""),
    series_id: int | None = Form(None),
    new_series_title: str = Form(""),
    is_standalone: str = Form(""),
    continuation_from_episode_id: str = Form(""),
    character_ids: list[int] = Form(default=[]),
    target_duration_sec: int = Form(15),
    title: str = Form(""),
) -> HTMLResponse:
    """Handle form submission and return a polling job-status partial."""

    standalone_flag = is_standalone.lower() in {"true", "on", "1", "yes"}
    resolved_theme_id = int(theme_id) if theme_id else None
    continuation_id = int(continuation_from_episode_id) if continuation_from_episode_id else None
    resolved_series_id = series_id
    if new_series_title.strip() and not standalone_flag and resolved_series_id is None:
        new_series = create_series(db, title=new_series_title.strip())
        resolved_series_id = new_series.id

    payload = EpisodeCreate(
        user_prompt=user_prompt,
        theme_id=resolved_theme_id,
        series_id=resolved_series_id,
        continuation_from_episode_id=continuation_id,
        character_ids=character_ids,
        target_duration_sec=target_duration_sec,
        title=title or None,
        is_standalone=standalone_flag,
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
