"""Theme schema definitions."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ThemeRead(BaseModel):
    """Response payload for a theme catalog item."""

    id: int
    key: str
    label: str
    description: str
    active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
