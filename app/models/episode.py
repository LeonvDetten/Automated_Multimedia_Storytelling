"""Episode and episode-character linking models."""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Episode(Base):
    """Single generated episode stored with optional continuation linkage."""

    __tablename__ = "episodes"

    id: Mapped[int] = mapped_column(primary_key=True)
    series_id: Mapped[int] = mapped_column(ForeignKey("story_series.id", ondelete="RESTRICT"), nullable=False, index=True)
    episode_number: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    user_prompt: Mapped[str] = mapped_column(Text, nullable=False)
    theme_id: Mapped[int] = mapped_column(ForeignKey("themes.id", ondelete="RESTRICT"), nullable=False)
    continuation_from_episode_id: Mapped[int | None] = mapped_column(
        ForeignKey("episodes.id", ondelete="SET NULL"), nullable=True
    )
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    script_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    target_duration_sec: Mapped[int] = mapped_column(Integer, nullable=False, default=15, server_default="15")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="draft", server_default="draft")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    series = relationship("StorySeries", back_populates="episodes")
    theme = relationship("Theme")
    continuation_from = relationship("Episode", remote_side=[id])
    characters = relationship("EpisodeCharacter", back_populates="episode", cascade="all, delete-orphan")
    jobs = relationship("Job", back_populates="episode", cascade="all, delete-orphan")

    __table_args__ = (UniqueConstraint("series_id", "episode_number", name="uq_episode_series_number"),)


class EpisodeCharacter(Base):
    """Join table assigning characters to an episode."""

    __tablename__ = "episode_characters"

    episode_id: Mapped[int] = mapped_column(ForeignKey("episodes.id", ondelete="CASCADE"), primary_key=True)
    character_id: Mapped[int] = mapped_column(ForeignKey("characters.id", ondelete="RESTRICT"), primary_key=True)
    role: Mapped[str] = mapped_column(String(64), nullable=False, default="support", server_default="support")

    episode = relationship("Episode", back_populates="characters")
    character = relationship("Character")
