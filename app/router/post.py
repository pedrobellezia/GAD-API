from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models import Post, User, UserType
from app.router.media import media_read_response
from app.schemas import (
    CommentCreate,
    CommentRead,
    DetailsResponse,
    PostCreate,
    PostFilter,
    PostMediaRead,
    PostRead,
    PostStatusUpdate,
    PostUpdate,
    PostWriterUpdate,
)
from app.services import post as post_service
from app.services.comment import create_comment, delete_comment, get_comments

router = APIRouter()


def post_read_response(post: Post, request: Request) -> PostRead:
    response = PostRead.model_validate(post)
    medias = [
        PostMediaRead(
            position=pm.position,
            media=media_read_response(pm.media, request),
        )
        for pm in post.medias
    ]
    return response.model_copy(update={"medias": medias})


@router.get(
    "/{post_id}/comments",
    status_code=status.HTTP_200_OK,
    response_model=list[CommentRead],
)
async def get_post_comments_route(
    post_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user()),
):
    return await get_comments(db=db, post_id=post_id, user=user)


@router.post(
    "/{post_id}/comments",
    status_code=status.HTTP_201_CREATED,
    response_model=CommentRead,
)
async def create_post_comment_route(
    post_id: UUID,
    comment_data: CommentCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user()),
):
    return await create_comment(
        db=db,
        post_id=post_id,
        user=user,
        comment_data=comment_data,
    )


@router.delete(
    "/{post_id}/comments/{comment_id}",
    status_code=status.HTTP_200_OK,
    response_model=DetailsResponse,
)
async def delete_post_comment_route(
    post_id: UUID,
    comment_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user()),
):
    await delete_comment(
        db=db,
        post_id=post_id,
        comment_id=comment_id,
        user=user,
    )
    return {"details": "Comentário removido com sucesso"}


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=PostRead,
    summary="Criar novo post",
)
async def create_post_route(
    post_data: PostCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user(UserType.writer)),
):
    post = await post_service.create_post(
        db=db,
        user=user,
        post_data=post_data,
    )
    return post_read_response(post, request)


@router.get(
    "",
    status_code=status.HTTP_200_OK,
    response_model=list[PostRead],
    summary="Listar posts",
)
async def get_posts_route(
    request: Request,
    filters: Annotated[PostFilter, Query()],
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user()),
):
    posts = await post_service.get_posts(
        db=db,
        user=user,
        filters=filters,
    )
    return [post_read_response(post, request) for post in posts]


@router.get(
    "/{post_id}",
    status_code=status.HTTP_200_OK,
    response_model=PostRead,
    summary="Obter detalhes de um post",
)
async def get_post_by_id_route(
    post_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user()),
):
    post = await post_service.get_post_by_id(
        db=db,
        post_id=post_id,
        user=user,
    )
    return post_read_response(post, request)


@router.patch(
    "/{post_id}",
    status_code=status.HTTP_200_OK,
    response_model=PostRead,
    summary="Atualizar post",
)
async def update_post_route(
    post_id: UUID,
    post_data: PostUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user()),
):
    post = await post_service.update_post(
        db=db,
        user=user,
        post_id=post_id,
        post_data=post_data,
    )
    return post_read_response(post, request)


@router.patch(
    "/{post_id}/status",
    status_code=status.HTTP_200_OK,
    response_model=PostRead,
    summary="Alterar status do post",
)
async def transition_post_status_route(
    post_id: UUID,
    status_data: PostStatusUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user()),
):
    post = await post_service.transition_post_status(
        db=db,
        user=user,
        post_id=post_id,
        status_data=status_data,
    )
    return post_read_response(post, request)


@router.patch(
    "/{post_id}/writer",
    status_code=status.HTTP_200_OK,
    response_model=PostRead,
    summary="Alterar redator do post",
)
async def update_post_writer_route(
    post_id: UUID,
    writer_data: PostWriterUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user(UserType.agency)),
):
    post = await post_service.update_post_writer(
        db=db,
        user=user,
        post_id=post_id,
        writer_data=writer_data,
    )
    return post_read_response(post, request)


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
