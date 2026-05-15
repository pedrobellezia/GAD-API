from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.dependencies import get_current_agency
from app.models import Agency, Client, InviteToken, User, Writer
from app.schemas import (
    AgencyRead,
    ClientRead,
    InviteTokenBatchCreate,
    InviteTokenPayload,
    InviteTokenRead,
    WriterRead,
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
        db, agency_id=user.id, kind=payload.kind, quantity=payload.quantity
    )
    await db.commit()
    return tokens


@router.delete(path="/me/invite_tokens/{token}", status_code=200)
async def route_agency_delete_invite_token(
    token: str,
    user: User = Depends(get_current_agency),
    db: AsyncSession = Depends(get_db),
):
    invite_token: InviteToken = await db.scalar(
        select(InviteToken).where(InviteToken.token == token)
    )
    if not token:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Token de convite nao encontrado",
        )
    if invite_token.agency_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Nao autorizado"
        )

    await db.delete(invite_token)
    await db.flush()
    await db.commit()


@router.post(path="/me/invite_tokens/unlink", status_code=200)
async def route_agency_unlink_invite_token(
    payload: InviteTokenPayload,
    user: User = Depends(get_current_agency),
    db: AsyncSession = Depends(get_db),
):
    invite_token = await db.scalar(
        select(InviteToken).where(InviteToken.token == payload.token)
    )

    if not invite_token:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Token de convite nao encontrado",
        )

    if invite_token.agency_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Nao autorizado"
        )

    invite_token.used_by = None
    await db.commit()
