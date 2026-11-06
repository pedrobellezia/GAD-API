from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import CustomAppError, CustomErrorType
from app.models import Comment, Post, User, UserType
from app.schemas import CommentCreate
from app.services.audit_log import record_audit


async def _get_post_for_comment(db: AsyncSession, post_id: UUID, user: User) -> Post:
    post = await db.scalar(select(Post).where(Post.id == post_id))
    if not post:
        raise CustomAppError(
            message="Post não encontrado",
            error_type=CustomErrorType.not_found,
        )

    authorized = (user.type == UserType.agency and post.agency_id == user.id) or (
        user.type == UserType.client and post.client_id == user.id
    )
    if not authorized:
        raise CustomAppError(
            message="Apenas a agência responsável ou o cliente do post pode acessar os comentários",
            error_type=CustomErrorType.forbidden,
        )
    return post


async def get_comments(db: AsyncSession, post_id: UUID, user: User) -> list[Comment]:
    await _get_post_for_comment(db, post_id, user)
    result = await db.scalars(
        select(Comment)
        .where(Comment.post_id == post_id)
        .order_by(Comment.created_at.asc())
    )
    return list(result.all())


async def create_comment(
    db: AsyncSession,
    post_id: UUID,
    user: User,
    comment_data: CommentCreate,
) -> Comment:
    post = await _get_post_for_comment(db, post_id, user)
    comment = Comment(
        post_id=post.id,
        author_id=user.id,
        content=comment_data.content,
    )
    db.add(comment)
    await db.flush()
    await record_audit(
        db,
        user=user,
        action="create",
        resource_type="comment",
        resource_id=comment.id,
        resource_name=f"Comentário do post {post.id}",
        agency_id=post.agency_id,
        message=f"{user.name} comentou no post '{post.title}'.",
    )
    await db.commit()
    await db.refresh(comment)
    return comment


async def delete_comment(
    db: AsyncSession, post_id: UUID, comment_id: UUID, user: User
) -> None:
    comment = await db.scalar(
        select(Comment).where(Comment.id == comment_id, Comment.post_id == post_id)
    )
    if not comment:
        raise CustomAppError(
            message="Comentário não encontrado",
            error_type=CustomErrorType.not_found,
        )

    post = await _get_post_for_comment(db, comment.post_id, user)
    if user.type != UserType.agency or post.agency_id != user.id:
        raise CustomAppError(
            message="Apenas a agência responsável pode remover comentários",
            error_type=CustomErrorType.forbidden,
        )

    await record_audit(
        db,
        user=user,
        action="delete",
        resource_type="comment",
        resource_id=comment.id,
        resource_name=f"Comentário do post {post.id}",
        agency_id=post.agency_id,
        message=f"{user.name} removeu um comentário do post '{post.title}'.",
    )
    await db.delete(comment)
    await db.commit()
