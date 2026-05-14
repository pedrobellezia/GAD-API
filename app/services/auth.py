from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import pswd_hasher
from app.models import User
from app.schemas import (
    RegisterPayload,
    LoginPayload,
    AgencyRegister,
    WriterRegister,
    ClientRegister,
)
from app.services import create_agency, create_writer, create_client


async def login(db: AsyncSession, payload: LoginPayload) -> bool:
    result: User | None = await db.scalar(
        select(User).where(User.email == payload.email)
    )
    if not result:
        return False

    bar = pswd_hasher.verify(payload.pswd, result.pswd)
    return bar


async def register(db: AsyncSession, payload: RegisterPayload) -> None:
    match payload:
        case AgencyRegister():
            await create_agency(db=db, agency_data=payload)

        case WriterRegister():
            await create_writer(db=db, writer_data=payload)

        case ClientRegister():
            await create_client(db=db, client_data=payload)
