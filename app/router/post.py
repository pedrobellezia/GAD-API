from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models import User, UserType
from app.schemas import (
    PostCreate,
    PostUpdate,
    PostRead,
    PostFilter,
    DetailsResponse,
)
from app.services import post as post_service

router = APIRouter()


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=PostRead,
    summary="Criar novo post",
)
async def create_post_route(
    post_data: PostCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user(UserType.writer)),
):
    return await post_service.create_post(
        db=db,
        user=user,
        post_data=post_data,
    )


@router.get(
    "",
    status_code=status.HTTP_200_OK,
    response_model=list[PostRead],
    summary="Listar posts",
)
async def get_posts_route(
    filters: PostFilter = Depends(),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user()),
):
    return await post_service.get_posts(
        db=db,
        user=user,
        filters=filters,
    )


@router.get(
    "/{post_id}",
    status_code=status.HTTP_200_OK,
    response_model=PostRead,
    summary="Obter detalhes de um post",
)
async def get_post_by_id_route(
    post_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user()),
):
    return await post_service.get_post_by_id(
        db=db,
        post_id=post_id,
        user=user,
    )


@router.patch(
    "/{post_id}",
    status_code=status.HTTP_200_OK,
    response_model=PostRead,
    summary="Atualizar post",
)
async def update_post_route(
    post_id: UUID,
    post_data: PostUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user()),
):
    return await post_service.update_post(
        db=db,
        user=user,
        post_id=post_id,
        post_data=post_data,
    )


@router.delete(
    "/{post_id}",
    status_code=status.HTTP_200_OK,
    response_model=DetailsResponse,
)
async def delete_post_route(
    post_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user()),
):
    await post_service.delete_post(
        db=db,
        user=user,
        post_id=post_id,
    )
    return DetailsResponse(details="Post excluído com sucesso")
