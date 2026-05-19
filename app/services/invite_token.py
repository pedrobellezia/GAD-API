import secrets
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import InviteToken


async def create_invite_tokens(
    db: AsyncSession,
    *,
    agency_id: UUID,
    quantity: int,
) -> list[InviteToken]:
    tokens: list[InviteToken] = []

    for _ in range(quantity):
        token = secrets.token_urlsafe(16)
        tokens.append(InviteToken(token=token, agency_id=agency_id))

    db.add_all(tokens)
    await db.flush()
    return tokens
