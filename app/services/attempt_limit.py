"""Limite de tentativas com erro (login, vínculo por token de convite).

Usa a tabela ``login_attempts``, identificando cada contador por uma chave
(ex.: hash de e-mail + IP no login, ``invite_link:<user_id>`` no convite).
"""

from datetime import UTC, datetime, timedelta

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import LoginAttempt


async def get_blocked_until(db: AsyncSession, key: str) -> datetime | None:
    """Retorna até quando a chave está bloqueada, ou ``None`` se não estiver."""
    attempt = await db.scalar(
        select(LoginAttempt).where(LoginAttempt.key == key).with_for_update()
    )
    if attempt and attempt.blocked_until and attempt.blocked_until > datetime.now(UTC):
        return attempt.blocked_until
    return None


async def record_failed_attempt(
    db: AsyncSession,
    key: str,
    *,
    max_attempts: int,
    window_minutes: int,
    block_minutes: int,
) -> None:
    """Conta um erro; ao chegar em ``max_attempts`` dentro da janela, bloqueia.

    Faz commit: precisa persistir mesmo que a requisição termine em erro.
    """
    now = datetime.now(UTC)
    attempt = await db.scalar(
        select(LoginAttempt).where(LoginAttempt.key == key).with_for_update()
    )
    if not attempt:
        attempt = LoginAttempt(key=key, failed_count=1, window_started_at=now)
        db.add(attempt)
    elif now - attempt.window_started_at >= timedelta(minutes=window_minutes):
        # Janela vencida: recomeça a contagem na mesma linha (a chave é única)
        attempt.failed_count = 1
        attempt.window_started_at = now
        attempt.blocked_until = None
    else:
        attempt.failed_count += 1
    if attempt.failed_count >= max_attempts:
        attempt.blocked_until = now + timedelta(minutes=block_minutes)
    await db.commit()


async def clear_attempts(db: AsyncSession, key: str, *, commit: bool = True) -> None:
    await db.execute(delete(LoginAttempt).where(LoginAttempt.key == key))
    if commit:
        await db.commit()
