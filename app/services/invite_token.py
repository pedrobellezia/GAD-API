import secrets
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import InviteToken


async def create_invite_tokens(
    db: AsyncSession,
    *,
    agency_id: UUID,
    quantity: int,
) -> None:
    tokens = [
        InviteToken(token=secrets.token_urlsafe(16), agency_id=agency_id)
        for _ in range(quantity)
    ]

    db.add_all(tokens)
