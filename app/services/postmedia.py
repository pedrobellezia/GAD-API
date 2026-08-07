from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.exceptions import CustomAppError, CustomErrorType
from app.models import PostMedia


async def add_media_to_post(
    db: AsyncSession,
    post_id: UUID,
    media_id: UUID,
    position: int = 0,
) -> PostMedia:
    post_media = PostMedia(
        post_id=post_id,
        media_id=media_id,
        position=position,
    )
    db.add(post_media)
    return post_media


async def remove_media_from_post(
    db: AsyncSession,
    post_id: UUID,
    media_id: UUID,
) -> None:
    post_media = await db.scalar(
        select(PostMedia).where(
            PostMedia.post_id == post_id,
            PostMedia.media_id == media_id,
        )
    )

    if not post_media:
        raise CustomAppError(
            message="Mídia não encontrada no post",
            error_type=CustomErrorType.not_found,
        )

    await db.delete(post_media)


async def get_medias_by_post(
    db: AsyncSession,
    post_id: UUID,
) -> list[PostMedia]:
    result = await db.execute(
        select(PostMedia)
        .options(selectinload(PostMedia.media))
        .where(PostMedia.post_id == post_id)
        .order_by(PostMedia.position)
    )
    return list(result.scalars().all())


async def update_media_position(
    db: AsyncSession,
    post_id: UUID,
    media_id: UUID,
    position: int,
) -> PostMedia:
    post_media = await db.scalar(
        select(PostMedia).where(
            PostMedia.post_id == post_id,
            PostMedia.media_id == media_id,
        )
    )

    if not post_media:
        raise CustomAppError(
            message="Mídia não encontrada no post",
            error_type=CustomErrorType.not_found,
        )

    post_media.position = position
    return post_media
