from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import CustomAppError, CustomErrorType
from app.models import Comment, Post, PostStatus, User, UserType
from app.schemas import CommentCreate
from app.services.audit_log import record_audit


async def _get_post_or_404(db: AsyncSession, post_id: UUID) -> Post:
    post = await db.scalar(select(Post).where(Post.id == post_id))
    if not post:
        raise CustomAppError(
            message="Post não encontrado",
            error_type=CustomErrorType.not_found,
        )
    return post


def _can_read_post_comments(post: Post, user: User) -> bool:
    if user.type == UserType.agency:
        return post.agency_id == user.id
    if user.type == UserType.writer:
        return bool(user.writer and post.agency_id == user.writer.agency_id)
    if user.type == UserType.designer:
        return bool(user.designer and post.agency_id == user.designer.agency_id)
    if user.type == UserType.client:
        return post.client_id == user.id and post.status != PostStatus.draft
    return False


def _can_write_post_comment(post: Post, user: User) -> bool:
    if user.type == UserType.agency:
        return post.agency_id == user.id
    if user.type == UserType.writer:
        return post.writer_id == user.id
    if user.type == UserType.client:
        return post.client_id == user.id and post.status != PostStatus.draft
    return False


async def get_comments(db: AsyncSession, post_id: UUID, user: User) -> list[Comment]:
    post = await _get_post_or_404(db, post_id)
    if not _can_read_post_comments(post, user):
        raise CustomAppError(
            message="Você não tem permissão para visualizar os comentários deste post",
            error_type=CustomErrorType.forbidden,
        )
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
    post = await _get_post_or_404(db, post_id)
    if not _can_write_post_comment(post, user):
        raise CustomAppError(
            message="Apenas a agência responsável, o redator autor ou o cliente do post podem comentar",
            error_type=CustomErrorType.forbidden,
        )
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
        resource_name=post.title,
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

    post = await _get_post_or_404(db, comment.post_id)
    is_agency_owner = user.type == UserType.agency and post.agency_id == user.id
    is_comment_author = comment.author_id == user.id and _can_write_post_comment(
        post, user
    )
    if not (is_agency_owner or is_comment_author):
        raise CustomAppError(
            message="Apenas a agência responsável ou o autor do comentário podem removê-lo",
            error_type=CustomErrorType.forbidden,
        )

    await record_audit(
        db,
        user=user,
        action="delete",
        resource_type="comment",
        resource_id=comment.id,
        resource_name=post.title,
        agency_id=post.agency_id,
        message=f"{user.name} removeu um comentário do post '{post.title}'.",
    )
    await db.delete(comment)
    await db.commit()
