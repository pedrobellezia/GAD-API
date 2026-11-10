from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models import User, UserType
from app.schemas import (
    AgencyRead,
    ClientRead,
    DesignerRead,
    DetailsResponse,
    ProfileUpdatePayload,
    WriterRead,
)
from app.services.agency import get_agency_me
from app.services.client import get_client_me
from app.services.designer import get_designer_me
from app.services.media import get_media_path
from app.services.user import (
    deactivate_user,
    remove_avatar,
    update_avatar,
    update_profile,
)
from app.services.writer import get_writer_me

router = APIRouter()


async def _load_profile_response(db: AsyncSession, user: User):
    match user.type:
        case UserType.agency:
            return await get_agency_me(db=db, user_id=user.id)
        case UserType.client:
            return await get_client_me(db=db, user_id=user.id)
        case UserType.writer:
            return await get_writer_me(db=db, user_id=user.id)
        case UserType.designer:
            return await get_designer_me(db=db, user_id=user.id)
        case _:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tipo de usuário inválido",
            )


@router.get(
    path="",
    status_code=status.HTTP_200_OK,
    response_model=ClientRead | WriterRead | AgencyRead | DesignerRead,
)
async def route_get_me(
    user: User = Depends(get_current_user()),
    db: AsyncSession = Depends(get_db),
):
    return await _load_profile_response(db, user)


@router.patch(
    path="",
    status_code=status.HTTP_200_OK,
    response_model=ClientRead | WriterRead | AgencyRead | DesignerRead,
)
async def route_update_me(
    payload: ProfileUpdatePayload,
    user: User = Depends(get_current_user()),
    db: AsyncSession = Depends(get_db),
):
    await update_profile(db=db, user=user, name=payload.name, email=payload.email)
    return await _load_profile_response(db, user)


@router.put(
    path="/avatar",
    status_code=status.HTTP_200_OK,
    response_model=DetailsResponse,
)
async def route_update_avatar(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user()),
    db: AsyncSession = Depends(get_db),
):
    try:
        await update_avatar(db=db, user=user, file=file)
    finally:
        await file.close()
    return {"details": "Avatar atualizado com sucesso"}


@router.delete(
    path="/avatar",
    status_code=status.HTTP_200_OK,
    response_model=DetailsResponse,
)
async def route_delete_avatar(
    user: User = Depends(get_current_user()),
    db: AsyncSession = Depends(get_db),
):
    await remove_avatar(db=db, user=user)
    return {"details": "Avatar removido com sucesso"}


@router.get(path="/avatar", response_class=FileResponse)
async def route_get_avatar(
    user: User = Depends(get_current_user()),
):
    if not user.avatar:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Avatar não encontrado",
        )
    path = get_media_path(user.avatar)
    if not path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Avatar não encontrado",
        )
    return FileResponse(path=path)


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
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="A desativação de agências não está disponível",
        )

    await deactivate_user(db=db, user=user)
    return {"details": "Usuário desativado com sucesso"}
