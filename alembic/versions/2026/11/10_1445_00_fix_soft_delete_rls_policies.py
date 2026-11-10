"""fix soft delete rls policies

Revision ID: 9a4b8c2d1e55
Revises: 7c1e4a9b2d33
"""

from collections.abc import Sequence

from alembic import op

revision: str = "9a4b8c2d1e55"
down_revision: str | Sequence[str] | None = "7c1e4a9b2d33"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("""
        GRANT SELECT, INSERT, UPDATE, DELETE
        ON ALL TABLES IN SCHEMA public
        TO dml_role;
    """)
    op.execute("""
        ALTER DEFAULT PRIVILEGES IN SCHEMA public
        GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO dml_role;
    """)

    op.execute("""
        CREATE OR REPLACE FUNCTION soft_delete_user(p_user_id UUID)
        RETURNS VOID
        LANGUAGE sql
        SECURITY DEFINER
        SET search_path = public
        AS $$
            UPDATE users
            SET deleted_at = NOW(),
                updated_at = NOW()
            WHERE id = p_user_id;
        $$;
    """)
    op.execute("REVOKE ALL ON FUNCTION soft_delete_user(UUID) FROM PUBLIC;")
    op.execute("GRANT EXECUTE ON FUNCTION soft_delete_user(UUID) TO dml_role;")

    op.execute("DROP POLICY IF EXISTS hide_soft_deleted_designers ON designers;")
    op.execute("DROP POLICY IF EXISTS hide_soft_deleted_agencies ON agencies;")
    op.execute("DROP POLICY IF EXISTS hide_soft_deleted_writers ON writers;")
    op.execute("DROP POLICY IF EXISTS hide_soft_deleted_clients ON clients;")
    op.execute("DROP POLICY IF EXISTS hide_soft_deleted_users ON users;")

    op.execute("""
        CREATE POLICY hide_soft_deleted_users
            ON users
            AS PERMISSIVE
            FOR ALL
            USING (
                users.deleted_at IS NULL
            )
            WITH CHECK (true);
    """)
    op.execute("""
        CREATE POLICY hide_soft_deleted_clients
            ON clients
            AS PERMISSIVE
            FOR ALL
            USING (
                EXISTS (
                    SELECT 1
                    FROM users
                    WHERE users.id = clients.id
                      AND users.deleted_at IS NULL
                )
            );
    """)
    op.execute("""
        CREATE POLICY hide_soft_deleted_writers
            ON writers
            AS PERMISSIVE
            FOR ALL
            USING (
                EXISTS (
                    SELECT 1
                    FROM users
                    WHERE users.id = writers.id
                      AND users.deleted_at IS NULL
                )
            );
    """)
    op.execute("""
        CREATE POLICY hide_soft_deleted_agencies
            ON agencies
            AS PERMISSIVE
            FOR ALL
            USING (
                EXISTS (
                    SELECT 1
                    FROM users
                    WHERE users.id = agencies.id
                      AND users.deleted_at IS NULL
                )
            );
    """)
    op.execute("""
        CREATE POLICY hide_soft_deleted_designers
            ON designers
            AS PERMISSIVE
            FOR ALL
            USING (
                EXISTS (
                    SELECT 1
                    FROM users
                    WHERE users.id = designers.id
                      AND users.deleted_at IS NULL
                )
            );
    """)


def downgrade() -> None:
    op.execute("DROP FUNCTION IF EXISTS soft_delete_user(UUID);")

    op.execute("DROP POLICY IF EXISTS hide_soft_deleted_designers ON designers;")
    op.execute("DROP POLICY IF EXISTS hide_soft_deleted_agencies ON agencies;")
    op.execute("DROP POLICY IF EXISTS hide_soft_deleted_writers ON writers;")
    op.execute("DROP POLICY IF EXISTS hide_soft_deleted_clients ON clients;")
    op.execute("DROP POLICY IF EXISTS hide_soft_deleted_users ON users;")

    op.execute("""
        CREATE POLICY hide_soft_deleted_users
            ON users
            AS RESTRICTIVE
            FOR ALL
            USING (
                users.deleted_at IS NULL
            );
    """)
    op.execute("""
        CREATE POLICY hide_soft_deleted_clients
            ON clients
            AS RESTRICTIVE
            FOR ALL
            USING (
                EXISTS (
                    SELECT 1
                    FROM users
                    WHERE users.id = clients.id
                      AND users.deleted_at IS NULL
                )
            );
    """)
    op.execute("""
        CREATE POLICY hide_soft_deleted_writers
            ON writers
            AS RESTRICTIVE
            FOR ALL
            USING (
                EXISTS (
                    SELECT 1
                    FROM users
                    WHERE users.id = writers.id
                      AND users.deleted_at IS NULL
                )
            );
    """)
    op.execute("""
        CREATE POLICY hide_soft_deleted_agencies
            ON agencies
            AS RESTRICTIVE
            FOR ALL
            USING (
                EXISTS (
                    SELECT 1
                    FROM users
                    WHERE users.id = agencies.id
                      AND users.deleted_at IS NULL
                )
            );
    """)
    op.execute("""
        CREATE POLICY hide_soft_deleted_designers
            ON designers
            AS RESTRICTIVE
            FOR ALL
            USING (
                EXISTS (
                    SELECT 1
                    FROM users
                    WHERE users.id = designers.id
                      AND users.deleted_at IS NULL
                )
            );
    """)
