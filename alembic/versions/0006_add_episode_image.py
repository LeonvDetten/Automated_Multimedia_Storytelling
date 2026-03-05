"""Add image_url to episodes.

Revision ID: 0006_add_episode_image
Revises: 0005_add_episode_model
Create Date: 2026-03-05
"""

from alembic import op
import sqlalchemy as sa

revision = "0006_add_episode_image"
down_revision = "0005_add_episode_model"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("episodes", sa.Column("image_url", sa.String(length=512), nullable=True))


def downgrade() -> None:
    op.drop_column("episodes", "image_url")
