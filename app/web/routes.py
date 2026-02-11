"""Server-rendered web routes for phase 1."""

import json

from fastapi import APIRouter, BackgroundTasks, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.db.session import get_db
from app.models.episode import Episode, EpisodeCharacter
from app.models.story_series import StorySeries
from app.repositories.character_repository import (
    create_character,
    delete_character,
    get_character,
    list_all_characters,
    list_characters,
    update_character,
)
from app.schemas.character import CharacterCreate
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


def _render_characters_page(request: Request, db: Session, message: str | None = None, kind: str | None = None) -> HTMLResponse:
    """Render the character management page with optional feedback."""

    characters = list_all_characters(db)
    context = {
        "request": request,
        "characters": characters,
        "message": message,
        "message_kind": kind,
    }
    return templates.TemplateResponse("characters.html", context)


@router.get("/web/characters", response_class=HTMLResponse)
def characters_manage(request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    """Render the character management page."""

    return _render_characters_page(request, db)


@router.post("/web/characters/create", response_class=HTMLResponse)
def character_create_action(
    request: Request,
    db: Session = Depends(get_db),
    name: str = Form(...),
    speech_style: str = Form(...),
    description: str = Form(...),
    traits_json: str = Form(""),
    active: str = Form(""),
) -> HTMLResponse:
    """Create a character from the management page."""

    try:
        traits = json.loads(traits_json) if traits_json.strip() else {}
    except json.JSONDecodeError:
        return _render_characters_page(request, db, "Traits JSON is invalid.", "error")

    payload = {
        "name": name.strip(),
        "speech_style": speech_style.strip(),
        "description": description.strip(),
        "traits_json": traits,
        "active": active.lower() in {"true", "on", "1", "yes"},
    }

    if not payload["name"] or not payload["speech_style"] or not payload["description"]:
        return _render_characters_page(request, db, "Please fill in name, speech style, and description.", "error")

    create_character(db, payload=CharacterCreate(**payload))
    return _render_characters_page(request, db, "Character created.", "success")


@router.post("/web/characters/{character_id}/update", response_class=HTMLResponse)
def character_update_action(
    request: Request,
    character_id: int,
    db: Session = Depends(get_db),
    name: str = Form(...),
    speech_style: str = Form(...),
    description: str = Form(...),
    traits_json: str = Form(""),
    active: str = Form(""),
) -> HTMLResponse:
    """Update an existing character."""

    character = get_character(db, character_id)
    if not character:
        return _render_characters_page(request, db, "Character not found.", "error")

    try:
        traits = json.loads(traits_json) if traits_json.strip() else {}
    except json.JSONDecodeError:
        return _render_characters_page(request, db, "Traits JSON is invalid.", "error")

    update_character(
        db,
        character,
        name=name.strip(),
        speech_style=speech_style.strip(),
        description=description.strip(),
        traits_json=traits,
        active=active.lower() in {"true", "on", "1", "yes"},
    )
    return _render_characters_page(request, db, "Character updated.", "success")


@router.post("/web/characters/{character_id}/delete", response_class=HTMLResponse)
def character_delete_action(
    request: Request,
    character_id: int,
    db: Session = Depends(get_db),
    confirm_check: str = Form(""),
    confirm_text: str = Form(""),
) -> HTMLResponse:
    """Delete a character if it is not used by any episodes."""

    error = _confirm_or_error(confirm_check, confirm_text)
    if error:
        return _render_characters_page(request, db, error, "error")

    character = get_character(db, character_id)
    if not character:
        return _render_characters_page(request, db, "Character not found.", "error")

    usage_count = db.scalar(select(func.count()).select_from(EpisodeCharacter).where(EpisodeCharacter.character_id == character_id))
    if usage_count and usage_count > 0:
        return _render_characters_page(
            request,
            db,
            "Character is used in existing episodes. Remove those links first.",
            "error",
        )

    delete_character(db, character)
    return _render_characters_page(request, db, "Character deleted.", "success")


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
    temperature: str = Form("0.8"),
    max_output_tokens: str = Form("800"),
    model: str = Form("gpt-5-mini"),
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
        temperature=float(temperature) if temperature else None,
        max_output_tokens=int(max_output_tokens) if max_output_tokens else None,
        model=model,
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


@router.get("/web/episodes", response_class=HTMLResponse)
def episodes_overview(request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    """Render a list of all episodes and standalone movies."""

    statement = (
        select(Episode)
        .options(
            selectinload(Episode.series),
            selectinload(Episode.theme),
            selectinload(Episode.characters).selectinload(EpisodeCharacter.character),
        )
        .order_by(Episode.created_at.desc())
    )
    episodes = list(db.scalars(statement).all())
    context = {"request": request, "episodes": episodes}
    return templates.TemplateResponse("episodes_list.html", context)
