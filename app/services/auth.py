import hashlib
from datetime import UTC, datetime, timedelta

from fastapi import HTTPException, Request, status
from sqlalchemy import delete, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import (
    LOGIN_BLOCK_MINUTES,
    LOGIN_MAX_ATTEMPTS,
    LOGIN_WINDOW_MINUTES,
    create_token,
    pswd_hasher,
)
from app.models import LoginAttempt, User
from app.schemas import (
    AgencyCreate,
    ClientCreate,
    LoginPayload,
    RegisterPayload,
    WriterCreate,
)
from app.schemas.auth import ChangePasswordPayload
from app.schemas.designer import DesignerCreate
from app.services import create_agency
from app.services.audit_log import record_audit
from app.services.client import create_client
from app.services.designer import create_designer
from app.services.writer import create_writer


def _login_key(payload: LoginPayload, request: Request) -> str:
    client_host = request.client.host if request.client else "unknown"
    raw_key = f"{payload.email.lower()}:{client_host}"
    return hashlib.sha256(raw_key.encode()).hexdigest()


async def _is_login_blocked(db: AsyncSession, key: str) -> bool:
    attempt = await db.scalar(
        select(LoginAttempt).where(LoginAttempt.key == key).with_for_update()
    )
    return bool(
        attempt and attempt.blocked_until and attempt.blocked_until > datetime.now(UTC)
    )


async def _record_failed_login(db: AsyncSession, key: str) -> None:
    now = datetime.now(UTC)
    attempt = await db.scalar(
        select(LoginAttempt).where(LoginAttempt.key == key).with_for_update()
    )
    if not attempt or now - attempt.window_started_at >= timedelta(
        minutes=LOGIN_WINDOW_MINUTES
    ):
        attempt = LoginAttempt(
            key=key,
            failed_count=1,
            window_started_at=now,
        )
        db.add(attempt)
    else:
        attempt.failed_count += 1
        if attempt.failed_count >= LOGIN_MAX_ATTEMPTS:
            attempt.blocked_until = now + timedelta(minutes=LOGIN_BLOCK_MINUTES)
    await db.commit()


async def _clear_login_attempts(db: AsyncSession, key: str) -> None:
    await db.execute(delete(LoginAttempt).where(LoginAttempt.key == key))
    await db.commit()


async def login(db: AsyncSession, payload: LoginPayload, request: Request) -> str:
    key = _login_key(payload, request)
    if await _is_login_blocked(db, key):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Muitas tentativas de login. Tente novamente mais tarde.",
        )

    query = select(User).from_statement(text("SELECT * FROM get_user_for_auth(:email)"))
    result: User | None = (
        await db.execute(query, {"email": payload.email})
    ).scalar_one_or_none()

    if not result:
        await _record_failed_login(db, key)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais inválidas",
        )

    if not pswd_hasher.verify(payload.pswd, result.pswd):
        await _record_failed_login(db, key)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais inválidas",
        )

    await _clear_login_attempts(db, key)

    if result.deleted_at is not None:
        if payload.restore:
            await db.execute(
                text("SELECT restore_user(:email)"),
                {"email": payload.email},
            )
            await db.refresh(result)
            await db.refresh(result, [result.type.value])
            await record_audit(
                db,
                user=result,
                action="restore",
                resource_type="user",
                resource_id=result.id,
                resource_name=result.name,
                message=f"{result.name} restaurou a própria conta.",
            )
            await db.commit()
        else:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Conta desativada. Envie restore=true para confirmar a reativação.",
            )

    token = create_token(user_id=result.id)

    return token


async def register(db: AsyncSession, payload: RegisterPayload) -> None:
    match payload:
        case AgencyCreate():
            await create_agency(db=db, agency_data=payload)

        case WriterCreate():
            await create_writer(db=db, writer_data=payload)

        case ClientCreate():
            await create_client(db=db, client_data=payload)

        case DesignerCreate():
            await create_designer(db=db, designer_data=payload)


async def change_password(
    db: AsyncSession, user: User, payload: ChangePasswordPayload
) -> None:
    if not pswd_hasher.verify(payload.current_password, user.pswd):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Senha atual inválida")
    if payload.current_password == payload.new_password:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "A nova senha deve ser diferente"
        )

    user.pswd = pswd_hasher.hash(payload.new_password)
    await record_audit(
        db,
        user=user,
        action="password_change",
        resource_type="user",
        resource_id=user.id,
        resource_name=user.name,
        message=f"{user.name} alterou a própria senha.",
    )
    await db.commit()
