from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core import get_db, get_current_client
from app.models import Agency, Client, Writer, User
from app.schemas import (
    ClientRead,
    AgencyRead,
    WriterRead,
)

router = APIRouter()


@router.get(path="/me", response_model=ClientRead, status_code=200)
async def route_client_me(
    user: User = Depends(get_current_client),
    db: AsyncSession = Depends(get_db),
):
    client = await db.scalar(
        select(Client)
        .options(
            selectinload(Client.user),
            selectinload(Client.agency).selectinload(Agency.user),
        )
        .where(Client.id == user.id)
    )
    return client


@router.get(path="/me/agency", response_model=AgencyRead | None, status_code=200)
async def route_client_agency(
    user: User = Depends(get_current_client),
    db: AsyncSession = Depends(get_db),
):
    agency_id = user.client.agency_id if user.client else None
    if not agency_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cliente nao possui agencia",
        )

    agency = await db.scalar(
        select(Agency).options(selectinload(Agency.user)).where(Agency.id == agency_id)
    )
    return agency


@router.get(
    path="/me/agency/writers",
    response_model=list[WriterRead],
    status_code=200,
)
async def route_client_agency_writers(
    user: User = Depends(get_current_client),
    db: AsyncSession = Depends(get_db),
):
    agency_id = user.client.agency_id if user.client else None
    if not agency_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cliente nao possui agencia",
        )

    result = await db.scalars(
        select(Writer)
        .options(
            selectinload(Writer.user),
            selectinload(Writer.agency).selectinload(Agency.user),
        )
        .where(Writer.agency_id == agency_id)
    )
    return list(result.unique().all())
