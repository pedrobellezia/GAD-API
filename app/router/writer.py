from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.dependencies import get_current_writer
from app.models import Agency, Client, InviteToken, InviteTokenKind, User, Writer
from app.schemas import AgencyRead, ClientRead, InviteTokenPayload, WriterRead

router = APIRouter()


@router.get(path="/me", response_model=WriterRead, status_code=200)
async def route_writer_me(
    user: User = Depends(get_current_writer),
    db: AsyncSession = Depends(get_db),
):
    writer = await db.scalar(
        select(Writer)
        .options(
            selectinload(Writer.user),
            selectinload(Writer.agency).selectinload(Agency.user),
        )
        .where(Writer.id == user.id)
    )
    return writer


@router.get(path="/me/agency", response_model=AgencyRead | None, status_code=200)
async def route_writer_agency(
    user: User = Depends(get_current_writer),
    db: AsyncSession = Depends(get_db),
):
    agency_id = user.writer.agency_id if user.writer else None
    if not agency_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Writer nao possui agencia",
        )

    agency = await db.scalar(
        select(Agency).options(selectinload(Agency.user)).where(Agency.id == agency_id)
    )
    return agency


@router.get(
    path="/me/agency/clients",
    response_model=list[ClientRead],
    status_code=200,
)
async def route_writer_agency_clients(
    user: User = Depends(get_current_writer),
    db: AsyncSession = Depends(get_db),
):
    agency_id = user.writer.agency_id if user.writer else None
    if not agency_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Writer nao possui agencia",
        )

    result = await db.scalars(
        select(Client)
        .options(
            selectinload(Client.user),
            selectinload(Client.agency).selectinload(Agency.user),
        )
        .where(Client.agency_id == agency_id)
    )
    return list(result.unique().all())


@router.post(path="/me/agency/link", response_model=WriterRead, status_code=200)
async def route_writer_link_agency(
    payload: InviteTokenPayload,
    user: User = Depends(get_current_writer),
    db: AsyncSession = Depends(get_db),
):
    if user.writer.agency_id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Writer ja vinculado a uma agencia",
        )

    token: InviteToken = await db.scalar(
        select(InviteToken).where(InviteToken.token == payload.token)
    )

    if not token:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Token de convite invalido",
        )
    if token.kind != InviteTokenKind.writer:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token de convite nao permitido para writer",
        )
    if token.used_by:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Token de convite ja utilizado",
        )

    user.writer.agency_id = token.agency_id
    token.used_by = user

    await db.flush()
    await db.commit()


@router.post(path="/me/agency/unlink", status_code=200)
async def route_client_unlink_agency(
    user: User = Depends(get_current_writer),
    db: AsyncSession = Depends(get_db),
):
    if not user.writer or not user.writer.agency_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Writer nao possui agencia",
        )

    if user.token_info is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Writer nao possui token de convite vinculado",
        )

    user.token_info = None
    user.writer.agency_id = None
    await db.commit()

    return {"detail": "Cliente desvinculado com sucesso"}
