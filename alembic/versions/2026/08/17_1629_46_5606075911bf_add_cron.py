"""add cron

Revision ID: 5606075911bf
Revises: e39d1d7a75e2
Create Date: 2026-08-17 16:29:46.858809+00:00

"""
from typing import Sequence, Union
from alembic import op


# revision identifiers, used by Alembic.
revision: str = '5606075911bf'
down_revision: Union[str, Sequence[str], None] = 'e39d1d7a75e2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        SELECT cron.schedule(
            'delete_soft_deleted_users',
            '0 0 * * *',
            $cron$
            DELETE FROM users
            WHERE deleted_at IS NOT NULL
              AND deleted_at < NOW() - INTERVAL '1 month';
            $cron$
        );
    """)


def downgrade() -> None:
    op.execute("""
        SELECT cron.unschedule('delete_soft_deleted_users');
    """)
