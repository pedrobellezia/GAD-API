from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.dependencies import get_current_agency
from app.models import Agency, Client, InviteToken, User, Writer
from app.schemas import (
    AgencyRead,
    ClientReadNoAgency,
    InviteTokenBatchCreate,
    InviteTokenRead,
    WriterReadNoAgency,
)
from app.services import create_invite_tokens

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


@router.get(
    path="/me/clients", response_model=list[ClientReadNoAgency], status_code=200
)
async def route_agency_clients(
    user: User = Depends(get_current_agency),
    db: AsyncSession = Depends(get_db),
):
    result = await db.scalars(
        select(Client)
        .options(selectinload(Client.user))
        .where(Client.agency_id == user.id)
    )
    return list(result.unique().all())


@router.get(
    path="/me/writers", response_model=list[WriterReadNoAgency], status_code=200
)
async def route_agency_writers(
    user: User = Depends(get_current_agency),
    db: AsyncSession = Depends(get_db),
):
    result = await db.scalars(
        select(Writer)
        .options(selectinload(Writer.user))
        .where(Writer.agency_id == user.id)
    )
    return list(result.unique().all())


# unlink


@router.get(path="/me/clients/unlink/{client_id}", status_code=200)
async def route_agency_client_unlink(
    client_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_agency),
):
    client = await db.scalar(
        select(Client).where(Client.id == client_id).where(Client.agency_id == user.id)
    )

    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cliente nao encontrado",
        )

    client.agency_id = None
    await db.commit()
    return {"detail": "Cliente desvinculado com sucesso"}


@router.get(
    path="/me/writers/unlink/{writer_id}",
    response_model=list[WriterReadNoAgency],
    status_code=200,
)
async def route_agency_writer_unlink(
    writer_id: UUID,
    user: User = Depends(get_current_agency),
    db: AsyncSession = Depends(get_db),
):
    writer = await db.scalar(
        select(Writer).where(Writer.id == writer_id).where(Writer.agency_id == user.id)
    )

    if not writer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Writer nao encontrado",
        )

    writer.agency_id = None
    await db.commit()
    return {"detail": "Writer desvinculado com sucesso"}


# invite tokens
@router.get(
    path="/me/invite_tokens", response_model=list[InviteTokenRead], status_code=200
)
async def route_agency_invite_tokens(
    user: User = Depends(get_current_agency), db: AsyncSession = Depends(get_db)
):
    result = await db.scalars(
        select(InviteToken).where(InviteToken.agency_id == user.id)
    )
    return list(result.unique().all())


@router.post(
    path="/me/invite_tokens", response_model=list[InviteTokenRead], status_code=201
)
async def route_agency_create_invite_tokens(
    payload: InviteTokenBatchCreate,
    user: User = Depends(get_current_agency),
    db: AsyncSession = Depends(get_db),
):
    tokens = await create_invite_tokens(
        db, agency_id=user.id, quantity=payload.quantity
    )
    await db.commit()
    return tokens


@router.delete(path="/me/invite_tokens/{token}", status_code=200)
async def route_agency_delete_invite_token(
    token: str,
    user: User = Depends(get_current_agency),
    db: AsyncSession = Depends(get_db),
):
    invite_token = await db.scalar(
        select(InviteToken)
        .where(InviteToken.token == token)
        .where(InviteToken.agency_id == user.id)
    )
    if not invite_token:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Token de convite nao encontrado",
        )

    await db.delete(invite_token)
    await db.commit()
    return {"detail": "Token de convite removido com sucesso"}
