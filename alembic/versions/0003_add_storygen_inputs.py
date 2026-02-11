"""Add temperature and max_output_tokens to episodes."""

from alembic import op
import sqlalchemy as sa

revision = "0003_add_storygen_inputs"
down_revision = "0002_make_series_optional"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add story generation input columns to episodes."""

    op.add_column("episodes", sa.Column("temperature", sa.Float(), nullable=True))
    op.add_column("episodes", sa.Column("max_output_tokens", sa.Integer(), nullable=True))


def downgrade() -> None:
    """Remove story generation input columns from episodes."""

    op.drop_column("episodes", "max_output_tokens")
    op.drop_column("episodes", "temperature")
