"""Episode schema definitions."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class EpisodeCreate(BaseModel):
    """Payload to create a new phase 1 episode job."""

    user_prompt: str = Field(min_length=1)
    theme_id: int
    series_id: int | None = None
    continuation_from_episode_id: int | None = None
    character_ids: list[int] = Field(default_factory=list)
    target_duration_sec: int = Field(default=15, ge=5, le=120)
    title: str | None = None


class EpisodeRead(BaseModel):
    """Response payload for episode data."""

    id: int
    series_id: int
    episode_number: int
    title: str
    user_prompt: str
    theme_id: int
    continuation_from_episode_id: int | None
    summary: str | None
    script_text: str | None
    target_duration_sec: int
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EpisodeCreateResponse(BaseModel):
    """Response payload returned after episode/job creation."""

    episode_id: int
    job_id: int
