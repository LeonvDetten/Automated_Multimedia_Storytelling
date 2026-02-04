"""Background job schema definitions."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class JobRead(BaseModel):
    """Response payload for job tracking."""

    id: int
    episode_id: int
    type: str
    status: str
    progress_pct: int
    step: str
    error_message: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
