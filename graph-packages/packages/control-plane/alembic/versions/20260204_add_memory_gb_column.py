"""Add memory_gb column to instances table.

This migration supports Phase 3: Dynamic Memory Upgrade feature which allows
in-place memory increases for running instances.

Changes:
1. Adds memory_gb column (nullable integer, default NULL)
   - Stores current allocated memory in GB
   - Updated when instance is resized
   - Used for governance checks and monitoring

Revision ID: 8b3f7e2c1a9d
Revises: 440c6421ad9d
Create Date: 2026-02-04 12:00:00 UTC
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "8b3f7e2c1a9d"
down_revision: str = "440c6421ad9d"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add memory_gb column to instances table."""
    op.add_column(
        "instances",
        sa.Column("memory_gb", sa.Integer(), nullable=True),
    )


def downgrade() -> None:
    """Remove memory_gb column from instances table."""
    op.drop_column("instances", "memory_gb")
