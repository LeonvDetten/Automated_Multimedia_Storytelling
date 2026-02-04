"""Character schema definitions."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class CharacterCreate(BaseModel):
    """Payload to create a new character."""

    name: str = Field(min_length=1, max_length=128)
    speech_style: str = Field(min_length=1, max_length=255)
    traits_json: dict[str, Any] = Field(default_factory=dict)
    description: str = Field(min_length=1)
    active: bool = True


class CharacterRead(BaseModel):
    """Response payload for character data."""

    id: int
    name: str
    speech_style: str
    traits_json: dict[str, Any]
    description: str
    active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
