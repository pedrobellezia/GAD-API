from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models import InviteToken, User, UserType
from app.schemas import (
    DetailsResponse,
    InviteTokenBatchCreate,
    InviteTokenRead,
)
from app.services import create_invite_tokens

router = APIRouter()


@router.get(
    path="", response_model=list[InviteTokenRead], status_code=status.HTTP_200_OK
)
async def route_agency_invite_tokens(
    user: User = Depends(get_current_user(UserType.agency)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.scalars(
        select(InviteToken).where(InviteToken.agency_id == user.id)
    )
    return list(result.unique().all())


@router.post(
    path="", response_model=DetailsResponse, status_code=status.HTTP_201_CREATED
)
async def route_agency_create_invite_tokens(
    payload: InviteTokenBatchCreate,
    user: User = Depends(get_current_user(UserType.agency)),
    db: AsyncSession = Depends(get_db),
):
    await create_invite_tokens(db, agency_id=user.id, quantity=payload.quantity)
    await db.commit()
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
    return {"details": "Token de convite removido com sucesso"}
