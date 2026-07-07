from sqlalchemy import text, select
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi import HTTPException, status

from app.core import pswd_hasher, create_token
from app.models import User
from app.schemas import (
    RegisterPayload,
    LoginPayload,
    AgencyCreate,
    WriterCreate,
    ClientCreate,
)
from app.schemas.designer import DesignerCreate
from app.services import create_agency
from app.services.designer import create_designer
from app.services.writer import create_writer
from app.services.client import create_client


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
        await db.execute(
            text("SELECT restore_user(:email)"),
            {"email": payload.email},
        )
        await db.commit()

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
