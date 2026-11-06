import secrets
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import CustomAppError, CustomErrorType
from app.models import InviteToken


async def get_invite_tokens(
    db: AsyncSession,
    *,
    agency_id: UUID,
) -> list[InviteToken]:
    result = await db.scalars(
        select(InviteToken).where(InviteToken.agency_id == agency_id)
    )
    return list(result.unique().all())


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
    await db.commit()


async def delete_invite_token(
    db: AsyncSession,
    *,
    agency_id: UUID,
    token: str,
) -> None:
    invite_token = await db.scalar(
        select(InviteToken)
        .where(InviteToken.token == token)
        .where(InviteToken.agency_id == agency_id)
    )
    if not invite_token:
        raise CustomAppError(
            message="Token de convite nao encontrado",
            error_type=CustomErrorType.not_found,
        )

    await db.delete(invite_token)
    await db.commit()
