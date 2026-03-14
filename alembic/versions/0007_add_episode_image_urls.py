"""Add image_urls to episodes.

Revision ID: 0007_add_episode_image_urls
Revises: 0006_add_episode_image
Create Date: 2026-03-14
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "0007_add_episode_image_urls"
down_revision = "0006_add_episode_image"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    cols = [c["name"] for c in inspector.get_columns("episodes")] if "episodes" in inspector.get_table_names() else []
    if "image_urls" not in cols:
        op.add_column("episodes", sa.Column("image_urls", sa.Text(), nullable=True))


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    cols = [c["name"] for c in inspector.get_columns("episodes")] if "episodes" in inspector.get_table_names() else []
    if "image_urls" in cols:
        op.drop_column("episodes", "image_urls")
