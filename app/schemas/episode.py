"""Episode schema definitions."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

StoryModel = Literal["gpt-4.1-mini", "gpt-4o-mini", "gpt-5-mini"]


class EpisodeCreate(BaseModel):
    """Payload to create a new phase 1 episode job."""

    user_prompt: str = Field(min_length=1)
    theme_id: int | None = None
    series_id: int | None = None
    continuation_from_episode_id: int | None = None
    character_ids: list[int] = Field(default_factory=list)
    target_duration_sec: int = Field(default=15, ge=5, le=120)
    temperature: float | None = Field(default=None, ge=0.0, le=1.5)
    max_output_tokens: int | None = Field(default=None, ge=50, le=4000)
    model: StoryModel = "gpt-4.1-mini"
    title: str | None = None
    is_standalone: bool = False


class EpisodeRead(BaseModel):
    """Response payload for episode data."""

    id: int
    series_id: int | None
    episode_number: int
    title: str
    user_prompt: str
    theme_id: int
    continuation_from_episode_id: int | None
    summary: str | None
    script_text: str | None
    target_duration_sec: int
    temperature: float | None
    max_output_tokens: int | None
    temperature_applied: bool | None
    model: str | None
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EpisodeCreateResponse(BaseModel):
    """Response payload returned after episode/job creation."""

    episode_id: int
    job_id: int
