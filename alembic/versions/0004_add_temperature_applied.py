"""Add temperature_applied to episodes."""

from alembic import op
import sqlalchemy as sa

revision = "0004_add_temperature_applied"
down_revision = "0003_add_storygen_inputs"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add temperature_applied to episodes."""

    op.add_column("episodes", sa.Column("temperature_applied", sa.Boolean(), nullable=True))


def downgrade() -> None:
    """Remove temperature_applied from episodes."""

    op.drop_column("episodes", "temperature_applied")
