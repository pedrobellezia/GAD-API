from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models import User, UserType, Client, Writer, Designer
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
    unlink_member,
    get_member_agency,
    get_my_clients,
    get_my_writers,
    get_my_designers,
)
from app.services.user import get_profile

router = APIRouter()


def _get_linked_member(user: User) -> Writer | Client | Designer | None:
    match user.type:
        case UserType.writer:
            return user.writer
        case UserType.client:
            return user.client
        case UserType.designer:
            return user.designer
        case _:
            return None


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
    member = _get_linked_member(user)
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
    member = _get_linked_member(user)
    await unlink_member(db=db, member=member)
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
    member = _get_linked_member(user)
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
    member = await get_profile(db=db, user_id=user_id)
    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Usuario nao encontrado"
        )
    await unlink_member(db=db, member=member, requesting_agency_id=user.id)
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
    if user.type == UserType.writer:
        return await get_my_clients(db=db, agency_id=user.writer.agency_id)
    elif user.type == UserType.designer:
        return await get_my_clients(db=db, agency_id=user.designer.agency_id)
    elif user.type == UserType.agency:
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
    if user.type == UserType.client:
        return await get_my_writers(db=db, agency_id=user.client.agency_id)
    elif user.type == UserType.designer:
        return await get_my_writers(db=db, agency_id=user.designer.agency_id)
    elif user.type == UserType.agency:
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
    if user.type == UserType.client:
        return await get_my_designers(db=db, agency_id=user.client.agency_id)
    elif user.type == UserType.writer:
        return await get_my_designers(db=db, agency_id=user.writer.agency_id)
    elif user.type == UserType.agency:
        return await get_my_designers(db=db, agency_id=user.id)
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Tipo de usuário inválido",
    )
