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
            # Generate image prompts (may be multiple) and call the image model
            image_prompts = result.get("image_prompts") or []
            saved_urls: list[str] = []
            if image_prompts:
                out_dir = os.path.join("app", "static", "generated")
                os.makedirs(out_dir, exist_ok=True)
                for idx, img_prompt in enumerate(image_prompts):
                    try:
                        # request a smaller resolution for speed and compact display
                        # use a supported image size for the OpenAI image model
                        img_result = client.generate_image(img_prompt, size="1024x1024")
                        b64 = img_result.get("b64")
                        url = img_result.get("url")
                        if b64:
                            filename = f"episode_{episode.id}_{idx}_{int(time.time())}.png"
                            filepath = os.path.join(out_dir, filename)
                            with open(filepath, "wb") as fh:
                                fh.write(base64.b64decode(b64))
                            saved_urls.append(f"/static/generated/{filename}")
                        elif url:
                            saved_urls.append(url)
                    except Exception as exc:
                        # record the failure in the job state and continue with remaining prompts
                        try:
                            update_job_state(db, job_id, status="running", progress_pct=80, step=f"image failed {idx+1}", error_message=str(exc))
                        except Exception:
                            pass
                        continue

                # persist the list of saved urls (join with separator for template parsing)
                if saved_urls:
                    episode.image_urls = "||".join(saved_urls)
                    # keep the first image_url for backward compatibility
                    episode.image_url = saved_urls[0]
                else:
                    episode.image_urls = None
                    try:
                        update_job_state(db, job_id, status="running", progress_pct=80, step="image generation skipped", error_message="no images produced")
                    except Exception:
                        pass
            if payload.temperature is None:
                episode.temperature_applied = None
            else:
                episode.temperature_applied = bool(result.get("temperature_applied"))
            episode.status = "generated"
            db.commit()

            # Preserve any existing error_message set during image generation
            job_obj = get_job(db, job_id)
            existing_error = job_obj.error_message if job_obj else None
            update_job_state(db, job_id, status="completed", progress_pct=100, step="completed", error_message=existing_error)
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
