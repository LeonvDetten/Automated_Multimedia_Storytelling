"""Job model to track asynchronous processing state."""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Job(Base):
    """Background task state for an episode pipeline run."""

    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(primary_key=True)
    episode_id: Mapped[int] = mapped_column(ForeignKey("episodes.id", ondelete="CASCADE"), nullable=False, index=True)
    type: Mapped[str] = mapped_column(String(64), nullable=False, default="phase1_stub", server_default="phase1_stub")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="queued", server_default="queued")
    progress_pct: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    step: Mapped[str] = mapped_column(String(128), nullable=False, default="queued", server_default="queued")
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    episode = relationship("Episode", back_populates="jobs")
