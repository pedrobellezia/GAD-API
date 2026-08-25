from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models import User, UserType
from app.schemas import (
    AgencyRead,
    ClientRead,
    DesignerRead,
    DetailsResponse,
    WriterRead,
)
from app.services import (
    get_my_clients,
    get_my_designers,
    get_my_writers,
    resolve_profile,
)
from app.services.agency import get_agency_me, unlink_member
from app.services.client import get_client_me
from app.services.designer import get_designer_me
from app.services.writer import get_writer_me

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
    match user.type:
        case UserType.agency:
            q = await get_agency_me(db=db, user_id=user.id)
        case UserType.client:
            q = await get_client_me(db=db, user_id=user.id)
        case UserType.writer:
            q = await get_writer_me(db=db, user_id=user.id)
        case UserType.designer:
            q = await get_designer_me(db=db, user_id=user.id)
        case _:
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
    if user.type == UserType.agency:
        users_list = [
            *(await get_my_writers(db, user.id)),
            *(await get_my_designers(db, user.id)),
            *(await get_my_clients(db, user.id)),
        ]
        for i in users_list:
            await unlink_member(db, i, requesting_agency_id=user.id)
    else:
        member = await resolve_profile(user)
        if member.agency_id:
            await unlink_member(db, member)
    user.deleted_at = datetime.now(UTC)
    await db.commit()
    return {"details": "Usuário deletado com sucesso"}
