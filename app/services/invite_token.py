import secrets
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import InviteToken, InviteTokenKind


def _generate_token() -> str:
    return secrets.token_urlsafe(16)


async def create_invite_tokens(
    db: AsyncSession,
    *,
    agency_id: UUID,
    kind: InviteTokenKind,
    quantity: int,
) -> list[InviteToken]:
    tokens: list[InviteToken] = []
    for _ in range(quantity):
        tokens.append(
            InviteToken(token=_generate_token(), kind=kind, agency_id=agency_id)
        )

    db.add_all(tokens)
    await db.flush()
    return tokens


async def get_invite_token_by_value(
    db: AsyncSession, *, token_value: str
) -> InviteToken | None:
    return await db.scalar(
        select(InviteToken)
        .options(selectinload(InviteToken.used_by))
        .where(InviteToken.token == token_value)
    )
