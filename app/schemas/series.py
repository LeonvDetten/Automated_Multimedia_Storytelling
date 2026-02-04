"""Story series schema definitions."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class StorySeriesRead(BaseModel):
    """Response payload for a story series item."""

    id: int
    title: str
    description: str
    language: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
