"""use exact 30-day cleanup window

Revision ID: 0f2d9c6e7a11
Revises: 8b8b2f3c1a21
"""

from typing import Sequence, Union

from alembic import op


revision: str = "0f2d9c6e7a11"
down_revision: Union[str, Sequence[str], None] = "8b8b2f3c1a21"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("SELECT cron.unschedule('delete_soft_deleted_users')")
    op.execute(
        """
        SELECT cron.schedule(
            'delete_soft_deleted_users',
            '0 0 * * *',
            $cron$
            DELETE FROM users
            WHERE deleted_at IS NOT NULL
              AND deleted_at < NOW() - INTERVAL '30 days';
            $cron$
        );
        """
    )


def downgrade() -> None:
    op.execute("SELECT cron.unschedule('delete_soft_deleted_users')")
    op.execute(
        """
        SELECT cron.schedule(
            'delete_soft_deleted_users',
            '0 0 * * *',
            $cron$
            DELETE FROM users
            WHERE deleted_at IS NOT NULL
              AND deleted_at < NOW() - INTERVAL '1 month';
            $cron$
        );
        """
    )
