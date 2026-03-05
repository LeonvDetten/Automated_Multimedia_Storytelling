"""Background job helpers for story generation."""

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.models.episode import Episode
from app.repositories.job_repository import get_job, update_job_state
from app.schemas.episode import EpisodeCreate
from app.storygen.openai_client import OpenAIClient
from app.storygen.story_service import generate_story
import base64
import os
import time


def _payload_from_episode(db: Session, episode: Episode) -> EpisodeCreate:
    """Build an EpisodeCreate payload from a stored episode record."""

    return EpisodeCreate(
        user_prompt=episode.user_prompt,
        theme_id=episode.theme_id,
        series_id=episode.series_id,
        continuation_from_episode_id=episode.continuation_from_episode_id,
        character_ids=[link.character_id for link in episode.characters],
        target_duration_sec=episode.target_duration_sec,
        title=episode.title,
        is_standalone=episode.series_id is None,
        temperature=episode.temperature,
        max_output_tokens=episode.max_output_tokens,
    )


def run_storygen_job(job_id: int) -> None:
    """Generate story text and persist it to the episode record."""

    settings = get_settings()
    api_key = settings.openai_api_key

    with SessionLocal() as db:
        job = get_job(db, job_id)
        if not job:
            return

        episode = job.episode
        if not episode:
            update_job_state(db, job_id, status="failed", progress_pct=100, step="missing episode", error_message="Episode not found.")
            return

        if not api_key:
            update_job_state(
                db,
                job_id,
                status="failed",
                progress_pct=100,
                step="missing configuration",
                error_message="OpenAI configuration missing.",
            )
            episode.status = "failed"
            db.commit()
            return

        update_job_state(db, job_id, status="running", progress_pct=10, step="building context")

        payload = _payload_from_episode(db, episode)
        model_name = episode.model or "gpt-4.1-mini"
        client = OpenAIClient(
            api_key=api_key,
            model=model_name,
            langfuse_public_key=settings.langfuse_public_key,
            langfuse_secret_key=settings.langfuse_secret_key,
            langfuse_host=settings.langfuse_host,
        )

        try:
            update_job_state(db, job_id, status="running", progress_pct=45, step="calling model")
            result = generate_story(db, payload, client)

            update_job_state(db, job_id, status="running", progress_pct=80, step="saving output")
            episode.script_text = result.get("text", "")
            # Generate an image prompt and call the image model
            image_prompt = result.get("image_prompt")
            if image_prompt:
                try:
                    img_result = client.generate_image(image_prompt)
                    b64 = img_result.get("b64")
                    url = img_result.get("url")
                    if b64:
                        # ensure directory exists
                        out_dir = os.path.join("app", "static", "generated")
                        os.makedirs(out_dir, exist_ok=True)
                        filename = f"episode_{episode.id}_{int(time.time())}.png"
                        filepath = os.path.join(out_dir, filename)
                        with open(filepath, "wb") as fh:
                            fh.write(base64.b64decode(b64))
                        episode.image_url = f"/static/generated/{filename}"
                    elif url:
                        # reference external URL directly
                        episode.image_url = url
                except Exception:
                    # do not fail the whole job if image generation fails
                    episode.image_url = None
            if payload.temperature is None:
                episode.temperature_applied = None
            else:
                episode.temperature_applied = bool(result.get("temperature_applied"))
            episode.status = "generated"
            db.commit()

            update_job_state(db, job_id, status="completed", progress_pct=100, step="completed")
        except Exception as exc:  # noqa: BLE001 - we want to surface any generation failure
            update_job_state(
                db,
                job_id,
                status="failed",
                progress_pct=100,
                step="failed",
                error_message=str(exc),
            )
            episode.status = "failed"
            db.commit()
