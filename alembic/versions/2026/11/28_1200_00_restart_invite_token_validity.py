"""restart validity of existing invite tokens

Os tokens de convite passam a valer 7 dias a partir de created_at. Os tokens
já existentes ganham created_at = agora, para não vencerem todos no deploy.

Revision ID: 4b7d1e9c2a60
Revises: 8e2c4f1a7b90
"""

from collections.abc import Sequence

from alembic import op

revision: str = "4b7d1e9c2a60"
down_revision: str | Sequence[str] | None = "8e2c4f1a7b90"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("UPDATE invite_tokens SET created_at = now()")


def downgrade() -> None:
    # A data original de criação não é recuperável; nada a desfazer
    pass
