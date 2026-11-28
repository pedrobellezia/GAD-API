import secrets
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import INVITE_TOKEN_ALPHABET, INVITE_TOKEN_LENGTH, INVITE_TOKEN_TTL_DAYS
from app.exceptions import CustomAppError, CustomErrorType
from app.models import InviteToken, User
from app.services.audit_log import record_audit


def invite_token_expiry_cutoff() -> datetime:
    """Tokens criados antes deste instante já venceram."""
    return datetime.now(UTC) - timedelta(days=INVITE_TOKEN_TTL_DAYS)


def normalize_invite_token(raw: str) -> set[str]:
    """Formas aceitas do token digitado.

    Os códigos novos são maiúsculos, então o texto digitado vale em maiúscula.
    A forma original é mantida para os tokens antigos (longos, com minúsculas).
    """
    cleaned = raw.strip()
    return {cleaned, cleaned.upper()}


def _new_code() -> str:
    return "".join(
        secrets.choice(INVITE_TOKEN_ALPHABET) for _ in range(INVITE_TOKEN_LENGTH)
    )


async def _generate_unique_codes(db: AsyncSession, quantity: int) -> list[str]:
    codes: set[str] = set()
    while len(codes) < quantity:
        candidates = {_new_code() for _ in range(quantity - len(codes))} - codes
        taken = set(
            await db.scalars(
                select(InviteToken.token).where(InviteToken.token.in_(candidates))
            )
        )
        codes |= candidates - taken
    return list(codes)


async def get_invite_tokens(
    db: AsyncSession,
    *,
    agency_id: UUID,
) -> list[InviteToken]:
    # Remove os vencidos da agência antes de listar
    await db.execute(
        delete(InviteToken)
        .where(InviteToken.agency_id == agency_id)
        .where(InviteToken.created_at < invite_token_expiry_cutoff())
    )
    await db.commit()
    result = await db.scalars(
        select(InviteToken)
        .where(InviteToken.agency_id == agency_id)
        .order_by(InviteToken.created_at.desc())
    )
    return list(result.unique().all())


async def create_invite_tokens(
    db: AsyncSession,
    *,
    user: User,
    quantity: int,
) -> None:
    tokens = [
        InviteToken(token=code, agency_id=user.id)
        for code in await _generate_unique_codes(db, quantity)
    ]

    db.add_all(tokens)
    await record_audit(
        db,
        user=user,
        action="create",
        resource_type="invite_token",
        agency_id=user.id,
        message=f"{user.name} criou {quantity} token(s) de convite.",
    )
    await db.commit()


async def delete_invite_token(
    db: AsyncSession,
    *,
    user: User,
    token: str,
) -> None:
    invite_token = await db.scalar(
        select(InviteToken)
        .where(InviteToken.token == token)
        .where(InviteToken.agency_id == user.id)
    )
    if not invite_token:
        raise CustomAppError(
            message="Token de convite nao encontrado",
            error_type=CustomErrorType.not_found,
        )

    await record_audit(
        db,
        user=user,
        action="delete",
        resource_type="invite_token",
        agency_id=user.id,
        message=f"{user.name} removeu um token de convite.",
    )
    await db.delete(invite_token)
    await db.commit()
