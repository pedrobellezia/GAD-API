from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

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
from app.services import create_agency, create_writer, create_client


async def login(db: AsyncSession, payload: LoginPayload) -> str:
    result: User | None = await db.scalar(
        select(User)
        .options(selectinload(User.agency))
        .where(User.email == payload.email)
    )
    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais inválidas",
        )

    bar = pswd_hasher.verify(payload.pswd, result.pswd)

    if not bar:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais inválidas",
        )

    token = create_token(
        user_id=result.id,
        **{
            "type": result.type.value,
            "agency_id": result.agency.id if result.agency else None,
        },
    )

    return token


async def register(db: AsyncSession, payload: RegisterPayload) -> None:
    match payload:
        case AgencyCreate():
            await create_agency(db=db, agency_data=payload)

        case WriterCreate():
            await create_writer(db=db, writer_data=payload)

        case ClientCreate():
            await create_client(db=db, client_data=payload)
