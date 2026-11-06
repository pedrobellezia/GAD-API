from fastapi import HTTPException, status
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import create_token, pswd_hasher
from app.models import User
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


async def login(db: AsyncSession, payload: LoginPayload) -> str:
    query = select(User).from_statement(text("SELECT * FROM get_user_for_auth(:email)"))
    result: User | None = (
        await db.execute(query, {"email": payload.email})
    ).scalar_one_or_none()

    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais inválidas",
        )

    if not pswd_hasher.verify(payload.pswd, result.pswd):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais inválidas",
        )

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
