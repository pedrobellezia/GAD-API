from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core import get_db, get_current_agency
from app.models import Agency, Client, Writer, User
from app.schemas import (
    AgencyRead,
    ClientRead,
    WriterRead,
)


from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


@router.get(path="/me", response_model=AgencyRead, status_code=200)
async def route_agency_me(
    user: User = Depends(get_current_agency),
    db: AsyncSession = Depends(get_db),
):
    agency = await db.scalar(
        select(Agency).options(selectinload(Agency.user)).where(Agency.id == user.id)
    )
    return agency


@router.get(path="/me/clients", response_model=list[ClientRead], status_code=200)
async def route_agency_clients(
    user: User = Depends(get_current_agency),
    db: AsyncSession = Depends(get_db),
):
    result = await db.scalars(
        select(Client)
        .options(
            selectinload(Client.user),
            selectinload(Client.agency).selectinload(Agency.user),
        )
        .where(Client.agency_id == user.id)
    )
    return list(result.unique().all())


@router.get(path="/me/writers", response_model=list[WriterRead], status_code=200)
async def route_agency_writers(
    user: User = Depends(get_current_agency),
    db: AsyncSession = Depends(get_db),
):
    result = await db.scalars(
        select(Writer)
        .options(
            selectinload(Writer.user),
            selectinload(Writer.agency).selectinload(Agency.user),
        )
        .where(Writer.agency_id == user.id)
    )
    return list(result.unique().all())
