"""add policies

Revision ID: c16caa61130d
Revises: f876482db3da
Create Date: 2026-08-17 16:29:34.654624+00:00

"""
from typing import Sequence, Union
from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'c16caa61130d'
down_revision: Union[str, Sequence[str], None] = 'f876482db3da'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TABLE agencies ENABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE agencies FORCE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE designers ENABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE designers FORCE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE writers ENABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE writers FORCE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE clients ENABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE clients FORCE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE users ENABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE users FORCE ROW LEVEL SECURITY;")

    op.execute("""
        CREATE POLICY hide_soft_deleted_users
            ON users
            AS RESTRICTIVE
            FOR ALL
            USING (
            users.deleted_at is NULL
            );
    """)
    op.execute("""
        CREATE POLICY hide_soft_deleted_clients
            ON clients
            AS RESTRICTIVE
            FOR ALL
            USING (
            EXISTS (SELECT 1
                    FROM users
                    WHERE users.id = clients.id
                      AND users.deleted_at IS NULL)
            );
    """)
    op.execute("""
        CREATE POLICY hide_soft_deleted_writers
            ON writers
            AS RESTRICTIVE
            FOR ALL
            USING (
            EXISTS (SELECT 1
                    FROM users
                    WHERE users.id = writers.id
                      AND users.deleted_at IS NULL)
            );
    """)
    op.execute("""
        CREATE POLICY hide_soft_deleted_agencies
            ON agencies
            AS RESTRICTIVE
            FOR ALL
            USING (
            EXISTS (SELECT 1
                    FROM users
                    WHERE users.id = agencies.id
                      AND users.deleted_at IS NULL)
            );
    """)
    op.execute("""
        CREATE POLICY hide_soft_deleted_designers
            ON designers
            AS RESTRICTIVE
            FOR ALL
            USING (
            EXISTS (SELECT 1
                    FROM users
                    WHERE users.id = designers.id
                      AND users.deleted_at IS NULL)
            );
    """)


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS hide_soft_deleted_designers ON designers;")
    op.execute("DROP POLICY IF EXISTS hide_soft_deleted_agencies ON agencies;")
    op.execute("DROP POLICY IF EXISTS hide_soft_deleted_writers ON writers;")
    op.execute("DROP POLICY IF EXISTS hide_soft_deleted_clients ON clients;")
    op.execute("DROP POLICY IF EXISTS hide_soft_deleted_users ON users;")

    op.execute("ALTER TABLE users NO FORCE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE users DISABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE clients NO FORCE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE clients DISABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE writers NO FORCE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE writers DISABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE designers NO FORCE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE designers DISABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE agencies NO FORCE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE agencies DISABLE ROW LEVEL SECURITY;")
