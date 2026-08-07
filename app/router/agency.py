from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.dependencies import get_current_user

from app.core.database import get_db
from app.models import User, UserType
from app.schemas import (
    DetailsResponse,
)
from app.services import get_profile

router = APIRouter()


@router.delete(
    path="/member/{user_id}/unlink",
    status_code=status.HTTP_200_OK,
    response_model=DetailsResponse,
)
async def route_agency_client_unlink(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user(UserType.agency)),
):
    profile = await get_profile(db=db, user_id=user_id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Usuario nao encontrado"
        )
    if not profile.agency_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Usuario nao esta vinculado a nenhuma agencia",
        )
    if profile.agency_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario nao esta vinculado a sua agencia",
        )
    profile.agency_id = None

    await db.commit()
    return {"details": "Usuario desvinculado com sucesso"}
