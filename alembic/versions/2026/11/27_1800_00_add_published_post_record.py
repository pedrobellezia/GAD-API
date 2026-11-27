"""add published post record and keep comments of deleted users

Revision ID: 8e2c4f1a7b90
Revises: 3f6d2b8a9c71
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "8e2c4f1a7b90"
down_revision: str | Sequence[str] | None = "3f6d2b8a9c71"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "posts", sa.Column("published_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column(
        "posts", sa.Column("published_client_name", sa.String(255), nullable=True)
    )
    op.add_column(
        "posts", sa.Column("published_writer_name", sa.String(255), nullable=True)
    )

    # Posts já publicados: data da última mudança de status para publicado no histórico
    # (ou updated_at, se não houver) e nomes de quem ainda estiver vinculado ao post.
    op.execute("""
        UPDATE posts p
        SET published_at = COALESCE(
            (
                SELECT MAX(a.created_at)
                FROM audit_logs a
                WHERE a.resource_type = 'post'
                  AND a.resource_id = p.id
                  AND a.action = 'status_change'
            ),
            p.updated_at
        )
        WHERE p.status = 'published';
    """)
    op.execute("""
        UPDATE posts p
        SET published_client_name = u.name
        FROM users u
        WHERE p.status = 'published' AND p.client_id = u.id;
    """)
    op.execute("""
        UPDATE posts p
        SET published_writer_name = u.name
        FROM users u
        WHERE p.status = 'published' AND p.writer_id = u.id;
    """)

    # Comentários deixam de ser apagados junto com a conta do autor
    op.execute("ALTER TABLE comments DROP CONSTRAINT IF EXISTS comments_author_id_fkey;")
    op.alter_column("comments", "author_id", existing_type=sa.Uuid(), nullable=True)
    op.create_foreign_key(
        "comments_author_id_fkey",
        "comments",
        "users",
        ["author_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.execute("ALTER TABLE comments DROP CONSTRAINT IF EXISTS comments_author_id_fkey;")
    op.execute("DELETE FROM comments WHERE author_id IS NULL;")
    op.alter_column("comments", "author_id", existing_type=sa.Uuid(), nullable=False)
    op.create_foreign_key(
        "comments_author_id_fkey",
        "comments",
        "users",
        ["author_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.drop_column("posts", "published_writer_name")
    op.drop_column("posts", "published_client_name")
    op.drop_column("posts", "published_at")
