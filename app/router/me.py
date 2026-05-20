from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.dependencies import get_current_user, get_current_member
from app.models import InviteToken, User, Agency
from app.schemas import (
    InviteTokenPayload,
    DetailsResponse,
    AgencyRead,
    ClientRead,
    WriterRead,
)
from app.services.agency import get_agency_me, get_my_clients, get_my_writers
from app.services.client import get_client_me
from app.services.writer import get_writer_me
from app.utils.types import Member

router = APIRouter()


@router.get(
    path="", status_code=200, response_model=ClientRead | WriterRead | AgencyRead
)
async def route_get_me(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if user.agency:
        q = await get_agency_me(db=db, user_id=user.id)
    elif user.client:
        q = await get_client_me(db=db, user_id=user.id)
        print(ClientRead.model_validate(q))
    elif user.writer:
        q = await get_writer_me(db=db, user_id=user.id)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tipo de usuário inválido",
        )
    return q


@router.post(path="/link", status_code=200, response_model=DetailsResponse)
async def route_writer_link_agency(
    payload: InviteTokenPayload,
    member: Member = Depends(get_current_member),
    db: AsyncSession = Depends(get_db),
):

    if member.agency_id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Usuário ja vinculado a uma agencia",
        )

    async with db.begin():
        token: InviteToken = await db.scalar(
            select(InviteToken)
            .where(InviteToken.token == payload.token)
            .with_for_update()
        )

        if not token:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Token de convite invalido",
            )

        member.agency_id = token.agency_id
        await db.flush()
        await db.delete(token)

    return {"details": "Usuário vinculado a agencia com sucesso"}


@router.post(path="/unlink", status_code=200, response_model=DetailsResponse)
async def route_writer_unlink_agency(
    member: Member = Depends(get_current_member),
    db: AsyncSession = Depends(get_db),
):

    if not member.agency_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário nao possui agencia",
        )

    member.agency_id = None
    await db.commit()
    return {"details": "Usuário desvinculado da agencia com sucesso"}


@router.get(path="/agency", response_model=AgencyRead, status_code=200)
async def route_writer_agency(
    member: Member = Depends(get_current_member),
    db: AsyncSession = Depends(get_db),
):
    agency_id = member.agency_id

    if not agency_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário nao possui agencia",
        )

    agency = await db.scalar(
        select(Agency).options(selectinload(Agency.user)).where(Agency.id == agency_id)
    )

    if not agency:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Não foi possível encontrar a agência do usuário",
        )

    return agency


@router.get("/clients", response_model=list[ClientRead], status_code=200)
async def route_get_clients(
    user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    if user.client:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Clientes nao tem acesso a este recurso",
        )
    elif user.writer:
        return await get_my_clients(db=db, agency_id=user.writer.agency_id)
    elif user.agency:
        return await get_my_clients(db=db, agency_id=user.id)
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Tipo de usuário inválido",
    )


@router.get("/writers", response_model=list[WriterRead], status_code=200)
async def route_get_writers(
    user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    if user.client:
        return await get_my_writers(db=db, agency_id=user.client.agency_id)
    elif user.writer:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Escritores nao tem acesso a este recurso",
        )
    elif user.agency:
        return await get_my_writers(db=db, agency_id=user.id)
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Tipo de usuário inválido",
    )
