from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models import User, UserType
from app.schemas import (
    DetailsResponse,
    InviteTokenPayload,
    AgencyRead,
    ClientRead,
    WriterRead,
    DesignerRead,
)
from app.services.agency import (
    link_member_by_token,
    unlink_member_self,
    get_member_agency,
    unlink_member_by_agency,
    get_my_clients,
    get_my_writers,
    get_my_designers,
)

router = APIRouter()


@router.post(
    path="/link",
    status_code=status.HTTP_200_OK,
    response_model=DetailsResponse,
)
async def route_link_agency(
    payload: InviteTokenPayload,
    user: User = Depends(
        get_current_user(UserType.writer, UserType.client, UserType.designer)
    ),
    db: AsyncSession = Depends(get_db),
):
    member = user.writer or user.client or user.designer
    await link_member_by_token(db=db, member=member, token_str=payload.token)
    return {"details": "Usuário vinculado a agencia com sucesso"}


@router.delete(
    path="/unlink",
    status_code=status.HTTP_200_OK,
    response_model=DetailsResponse,
)
async def route_unlink_agency_self(
    user: User = Depends(
        get_current_user(UserType.writer, UserType.client, UserType.designer)
    ),
    db: AsyncSession = Depends(get_db),
):
    member = user.writer or user.client or user.designer
    await unlink_member_self(db=db, member=member)
    return {"details": "Usuário desvinculado da agencia com sucesso"}


@router.get(
    path="/my",
    response_model=AgencyRead,
    status_code=status.HTTP_200_OK,
)
async def route_get_my_agency(
    user: User = Depends(
        get_current_user(UserType.writer, UserType.client, UserType.designer)
    ),
    db: AsyncSession = Depends(get_db),
):
    member = user.writer or user.client or user.designer
    return await get_member_agency(db=db, member=member)


@router.delete(
    path="/member/{user_id}/unlink",
    status_code=status.HTTP_200_OK,
    response_model=DetailsResponse,
)
async def route_agency_member_unlink(
    user_id: UUID,
    user: User = Depends(get_current_user(UserType.agency)),
    db: AsyncSession = Depends(get_db),
):
    await unlink_member_by_agency(db=db, agency_user_id=user.id, member_id=user_id)
    return {"details": "Usuario desvinculado com sucesso"}


@router.get(
    path="/clients",
    response_model=list[ClientRead],
    status_code=status.HTTP_200_OK,
)
async def route_get_clients(
    user: User = Depends(
        get_current_user(UserType.writer, UserType.agency, UserType.designer)
    ),
    db: AsyncSession = Depends(get_db),
):
    if user.writer:
        return await get_my_clients(db=db, agency_id=user.writer.agency_id)
    elif user.designer:
        return await get_my_clients(db=db, agency_id=user.designer.agency_id)
    elif user.agency:
        return await get_my_clients(db=db, agency_id=user.id)
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Tipo de usuário inválido",
    )


@router.get(
    path="/writers",
    response_model=list[WriterRead],
    status_code=status.HTTP_200_OK,
)
async def route_get_writers(
    user: User = Depends(
        get_current_user(UserType.client, UserType.agency, UserType.designer)
    ),
    db: AsyncSession = Depends(get_db),
):
    if user.client:
        return await get_my_writers(db=db, agency_id=user.client.agency_id)
    elif user.designer:
        return await get_my_writers(db=db, agency_id=user.designer.agency_id)
    elif user.agency:
        return await get_my_writers(db=db, agency_id=user.id)
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Tipo de usuário inválido",
    )


@router.get(
    path="/designers",
    response_model=list[DesignerRead],
    status_code=status.HTTP_200_OK,
)
async def route_get_designers(
    user: User = Depends(
        get_current_user(UserType.client, UserType.agency, UserType.writer)
    ),
    db: AsyncSession = Depends(get_db),
):
    if user.client:
        return await get_my_designers(db=db, agency_id=user.client.agency_id)
    elif user.writer:
        return await get_my_designers(db=db, agency_id=user.writer.agency_id)
    elif user.agency:
        return await get_my_designers(db=db, agency_id=user.id)
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Tipo de usuário inválido",
    )
