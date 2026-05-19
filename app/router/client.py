from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.dependencies import get_current_client
from app.models import Agency, Client, InviteToken, User, Writer
from app.schemas import (
    AgencyRead,
    ClientRead,
    InviteTokenPayload,
    WriterReadNoAgency,
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
    response_model=list[WriterReadNoAgency],
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
        .options(selectinload(Writer.user))
        .where(Writer.agency_id == agency_id)
    )
    return list(result.unique().all())


@router.post(path="/me/agency/link", status_code=200)
async def route_client_link_agency(
    payload: InviteTokenPayload,
    user: User = Depends(get_current_client),
    db: AsyncSession = Depends(get_db),
):

    if user.client.agency_id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cliente ja vinculado a uma agencia",
        )

    token: InviteToken = await db.scalar(
        select(InviteToken).where(InviteToken.token == payload.token)
    )

    if not token:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Token de convite invalido",
        )

    user.client.agency_id = token.agency_id

    await db.flush()
    await db.delete(token)
    await db.commit()


@router.post(path="/me/agency/unlink", status_code=200)
async def route_client_unlink_agency(
    user: User = Depends(get_current_client),
    db: AsyncSession = Depends(get_db),
):
    if not user.client or not user.client.agency_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cliente nao possui agencia",
        )

    user.client.agency_id = None
    await db.commit()

    return {"detail": "Cliente desvinculado com sucesso"}
