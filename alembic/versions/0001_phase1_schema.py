"""create phase 1 schema

Revision ID: 0001_phase1_schema
Revises:
Create Date: 2026-02-04 00:00:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0001_phase1_schema"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create the core relational schema for phase 1."""

    op.create_table(
        "themes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("key", sa.String(length=64), nullable=False),
        sa.Column("label", sa.String(length=128), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("key", name="uq_themes_key"),
    )

    op.create_table(
        "story_series",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("language", sa.String(length=16), nullable=False, server_default="en"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "characters",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("speech_style", sa.String(length=255), nullable=False),
        sa.Column("traits_json", sa.JSON(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "episodes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("series_id", sa.Integer(), nullable=False),
        sa.Column("episode_number", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("user_prompt", sa.Text(), nullable=False),
        sa.Column("theme_id", sa.Integer(), nullable=False),
        sa.Column("continuation_from_episode_id", sa.Integer(), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("script_text", sa.Text(), nullable=True),
        sa.Column("target_duration_sec", sa.Integer(), nullable=False, server_default="15"),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="draft"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["series_id"], ["story_series.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["theme_id"], ["themes.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["continuation_from_episode_id"], ["episodes.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("series_id", "episode_number", name="uq_episode_series_number"),
    )
    op.create_index("ix_episodes_series_id", "episodes", ["series_id"])

    op.create_table(
        "episode_characters",
        sa.Column("episode_id", sa.Integer(), nullable=False),
        sa.Column("character_id", sa.Integer(), nullable=False),
        sa.Column("role", sa.String(length=64), nullable=False, server_default="support"),
        sa.ForeignKeyConstraint(["episode_id"], ["episodes.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["character_id"], ["characters.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("episode_id", "character_id"),
    )

    op.create_table(
        "jobs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("episode_id", sa.Integer(), nullable=False),
        sa.Column("type", sa.String(length=64), nullable=False, server_default="phase1_stub"),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="queued"),
        sa.Column("progress_pct", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("step", sa.String(length=128), nullable=False, server_default="queued"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["episode_id"], ["episodes.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_jobs_episode_id", "jobs", ["episode_id"])


def downgrade() -> None:
    """Drop schema in reverse dependency order."""

    op.drop_index("ix_jobs_episode_id", table_name="jobs")
    op.drop_table("jobs")
    op.drop_table("episode_characters")
    op.drop_index("ix_episodes_series_id", table_name="episodes")
    op.drop_table("episodes")
    op.drop_table("characters")
    op.drop_table("story_series")
    op.drop_table("themes")
