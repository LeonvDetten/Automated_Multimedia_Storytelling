"""make series optional for standalone episodes

Revision ID: 0002_make_series_optional
Revises: 0001_phase1_schema
Create Date: 2026-02-11 00:00:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0002_make_series_optional"
down_revision: str | None = "0001_phase1_schema"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Allow episodes without a series for standalone stories."""

    op.alter_column(
        "episodes",
        "series_id",
        existing_type=sa.Integer(),
        nullable=True,
        existing_nullable=False,
    )


def downgrade() -> None:
    """Revert series_id to required."""

    op.alter_column(
        "episodes",
        "series_id",
        existing_type=sa.Integer(),
        nullable=False,
        existing_nullable=True,
    )
