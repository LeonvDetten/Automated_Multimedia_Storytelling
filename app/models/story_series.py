"""Story series model for linked episodes."""

from datetime import datetime

from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class StorySeries(Base):
    """A collection of episodes that belong to the same story line."""

    __tablename__ = "story_series"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")
    language: Mapped[str] = mapped_column(String(16), nullable=False, default="en", server_default="en")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    episodes = relationship("Episode", back_populates="series")
