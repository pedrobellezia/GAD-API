"""add functions

Revision ID: e39d1d7a75e2
Revises: c16caa61130d
Create Date: 2026-08-17 16:29:44.828674+00:00

"""
from typing import Sequence, Union
from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'e39d1d7a75e2'
down_revision: Union[str, Sequence[str], None] = 'c16caa61130d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        CREATE OR REPLACE FUNCTION get_user_for_auth(p_email TEXT)
        RETURNS users
        LANGUAGE sql
        STABLE
        SECURITY DEFINER
        SET search_path = public
        AS $$
            SELECT *
            FROM users
            WHERE email = p_email
            LIMIT 1;
        $$;
    """)

    op.execute("""
        REVOKE ALL
        ON FUNCTION get_user_for_auth(TEXT)
        FROM PUBLIC;
    """)

    op.execute("""
        GRANT EXECUTE
        ON FUNCTION get_user_for_auth(TEXT)
        TO dml_role;
    """)

    op.execute("""
        CREATE OR REPLACE FUNCTION restore_user(p_email TEXT)
        RETURNS VOID
        LANGUAGE sql
        SECURITY DEFINER
        SET search_path = public
        AS $$
            UPDATE users
            SET deleted_at = NULL
            WHERE email = p_email;
        $$;
    """)

    op.execute("""
        REVOKE ALL
        ON FUNCTION restore_user(TEXT)
        FROM PUBLIC;
    """)

    op.execute("""
        GRANT EXECUTE
        ON FUNCTION restore_user(TEXT)
        TO dml_role;
    """)


def downgrade() -> None:
    op.execute("""
        REVOKE ALL
        ON FUNCTION restore_user(TEXT)
        FROM PUBLIC;
    """)

    op.execute("""
        DROP FUNCTION IF EXISTS restore_user(TEXT);
    """)

    op.execute("""
        REVOKE ALL
        ON FUNCTION get_user_for_auth(TEXT)
        FROM PUBLIC;
    """)

    op.execute("""
        DROP FUNCTION IF EXISTS get_user_for_auth(TEXT);
    """)