"""Add pending_snapshot_id and waiting_for_snapshot status.

This migration supports the "Create Instance from Mapping" feature which allows
creating an instance that waits for a snapshot to be built before starting.

Changes:
1. Adds pending_snapshot_id column (nullable FK to snapshots.id)
2. Updates instances status CHECK constraint to include 'waiting_for_snapshot'

Revision ID: 440c6421ad9d
Revises: None
Create Date: 2026-01-27 15:02:43 UTC
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "440c6421ad9d"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add pending_snapshot_id column and update status constraint."""
    # Add pending_snapshot_id column
    # This column is set when an instance is created from a mapping and must
    # wait for a snapshot to be built before it can start
    op.add_column(
        "instances",
        sa.Column("pending_snapshot_id", sa.Integer(), nullable=True),
    )

    # Add foreign key constraint for pending_snapshot_id
    op.create_foreign_key(
        "fk_instances_pending_snapshot_id",
        "instances",
        "snapshots",
        ["pending_snapshot_id"],
        ["id"],
    )

    # Drop the existing status CHECK constraint
    # PostgreSQL requires dropping and recreating CHECK constraints to modify them
    op.drop_constraint("instances_status_check", "instances", type_="check")

    # Recreate status constraint with the new 'waiting_for_snapshot' value
    op.create_check_constraint(
        "instances_status_check",
        "instances",
        "status IN ('waiting_for_snapshot', 'starting', 'running', 'stopping', 'failed')",
    )


def downgrade() -> None:
    """Remove pending_snapshot_id column and revert status constraint."""
    # First, update any instances in 'waiting_for_snapshot' status to 'failed'
    # This ensures the constraint can be applied after downgrade
    op.execute(
        "UPDATE instances SET status = 'failed', "
        "error_message = 'Downgraded from waiting_for_snapshot status' "
        "WHERE status = 'waiting_for_snapshot'"
    )

    # Drop the status constraint with 'waiting_for_snapshot'
    op.drop_constraint("instances_status_check", "instances", type_="check")

    # Recreate original status constraint without 'waiting_for_snapshot'
    op.create_check_constraint(
        "instances_status_check",
        "instances",
        "status IN ('starting', 'running', 'stopping', 'failed')",
    )

    # Drop foreign key constraint for pending_snapshot_id
    op.drop_constraint(
        "fk_instances_pending_snapshot_id", "instances", type_="foreignkey"
    )

    # Drop pending_snapshot_id column
    op.drop_column("instances", "pending_snapshot_id")
