from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models import User, UserType
from app.schemas import (
    DetailsResponse,
    InviteTokenBatchCreate,
    InviteTokenRead,
)
from app.services import (
    create_invite_tokens,
    delete_invite_token,
    get_invite_tokens,
)

router = APIRouter()


@router.get(
    path="", response_model=list[InviteTokenRead], status_code=status.HTTP_200_OK
)
async def route_agency_invite_tokens(
    user: User = Depends(get_current_user(UserType.agency)),
    db: AsyncSession = Depends(get_db),
):
    return await get_invite_tokens(db, agency_id=user.id)


@router.post(
    path="", response_model=DetailsResponse, status_code=status.HTTP_201_CREATED
)
async def route_agency_create_invite_tokens(
    payload: InviteTokenBatchCreate,
    user: User = Depends(get_current_user(UserType.agency)),
    db: AsyncSession = Depends(get_db),
):
    await create_invite_tokens(db, agency_id=user.id, quantity=payload.quantity)
    return {"details": f"{payload.quantity} tokens de convite criados com sucesso"}


@router.delete(
    path="/{token}",
    status_code=status.HTTP_200_OK,
    response_model=DetailsResponse,
)
async def route_agency_delete_invite_token(
    token: str,
    user: User = Depends(get_current_user(UserType.agency)),
    db: AsyncSession = Depends(get_db),
):
    await delete_invite_token(db, agency_id=user.id, token=token)
    return {"details": "Token de convite removido com sucesso"}
