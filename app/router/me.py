from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models import User
from app.schemas import (
    DetailsResponse,
    AgencyRead,
    ClientRead,
    WriterRead,
    DesignerRead,
)
from app.services.agency import get_agency_me
from app.services.client import get_client_me
from app.services.writer import get_writer_me
from app.services.designer import get_designer_me

router = APIRouter()


@router.get(
    path="",
    status_code=status.HTTP_200_OK,
    response_model=ClientRead | WriterRead | AgencyRead | DesignerRead,
)
async def route_get_me(
    user: User = Depends(get_current_user()),
    db: AsyncSession = Depends(get_db),
):
    if user.agency:
        q = await get_agency_me(db=db, user_id=user.id)
    elif user.client:
        q = await get_client_me(db=db, user_id=user.id)
    elif user.writer:
        q = await get_writer_me(db=db, user_id=user.id)
    elif user.designer:
        q = await get_designer_me(db=db, user_id=user.id)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tipo de usuário inválido",
        )
    return q


@router.delete(
    path="",
    status_code=status.HTTP_200_OK,
    response_model=DetailsResponse,
)
async def route_delete_me(
    user: User = Depends(get_current_user()),
    db: AsyncSession = Depends(get_db),
):
    user.deleted_at = datetime.now(timezone.utc)
    await db.commit()
    return {"details": "Usuário deletado com sucesso"}
