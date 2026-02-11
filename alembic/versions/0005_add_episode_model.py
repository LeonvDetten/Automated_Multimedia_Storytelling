"""Add model to episodes."""

from alembic import op
import sqlalchemy as sa

revision = "0005_add_episode_model"
down_revision = "0004_add_temperature_applied"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add model to episodes."""

    op.add_column("episodes", sa.Column("model", sa.String(length=64), nullable=True))


def downgrade() -> None:
    """Remove model from episodes."""

    op.drop_column("episodes", "model")
