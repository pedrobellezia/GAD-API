"""add unaccent extension

Revision ID: 3f6d2b8a9c71
Revises: 9a4b8c2d1e55
"""

from collections.abc import Sequence

from alembic import op

revision: str = "3f6d2b8a9c71"
down_revision: str | Sequence[str] | None = "9a4b8c2d1e55"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Busca sem diferenciar acentos (ex.: "joao" encontra "João") no histórico
    op.execute("CREATE EXTENSION IF NOT EXISTS unaccent;")


def downgrade() -> None:
    op.execute("DROP EXTENSION IF EXISTS unaccent;")
