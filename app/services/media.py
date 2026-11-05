import asyncio
from pathlib import Path
from uuid import uuid4

import aiofiles
from fastapi import UploadFile
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core import (
    ALLOWED_FILE_TYPES,
    CHUNKS_PER_READ,
    LOCAL_STORAGE_PATH,
    MAX_FILE_BYTES,
    mime_detector,
)
from app.exceptions import CustomAppError, CustomErrorType
from app.models import (
    Designer,
    Media,
    MediaType,
    Post,
    PostMedia,
    PostStatus,
    User,
    UserType,
)
from app.schemas import MediaDesignerUpdate, MediaUpdate
from app.services.audit_log import record_audit


class MediaFileInfo(BaseModel):
    mime_type: str
    extension: str
    media_type: MediaType


async def validate_media_file(file: UploadFile) -> MediaFileInfo:
    mime, extension = await detect_file_type(file)

    if extension == ".mp4":
        media_type = MediaType.video
    else:
        media_type = MediaType.image

    return MediaFileInfo(mime_type=mime, extension=extension, media_type=media_type)


async def detect_file_type(file: UploadFile) -> tuple[str, str]:
    header = await file.read(2048)
    if not header:
        raise CustomAppError(
            message="Arquivo vazio ou corrompido",
            error_type=CustomErrorType.bad_request,
            filename=file.filename,
        )
    mime: str = mime_detector.from_buffer(header)
    await file.seek(0)

    if mime not in ALLOWED_FILE_TYPES:
        raise CustomAppError(
            message=f"Tipo de arquivo não suportado: {mime}",
            error_type=CustomErrorType.unsupported_media_type,
        )
    extension: str = ALLOWED_FILE_TYPES[mime]

    return mime, extension


async def store_media_file(file: UploadFile, extension: str):
    total_size: int = 0
    filename = f"{uuid4().hex}{extension}"
    full_path: Path = LOCAL_STORAGE_PATH / filename
    done = False

    try:
        async with aiofiles.open(full_path, "wb") as out_file:
            while chunk := await file.read(CHUNKS_PER_READ):
                total_size += len(chunk)

                if total_size > MAX_FILE_BYTES:
                    raise CustomAppError(
                        message=(
                            f"O arquivo {file.filename} excede o tamanho máximo permitido de {MAX_FILE_BYTES} bytes"
                        ),
                        error_type=CustomErrorType.payload_too_large,
                        filename=file.filename,
                    )

                await out_file.write(chunk)

        done = True
        return filename, total_size

    finally:
        if not done and full_path.exists():
            await asyncio.to_thread(full_path.unlink)


async def update_media_designer(
    db: AsyncSession,
    user: User,
    media_id,
    designer_data: MediaDesignerUpdate,
) -> Media:
    media = await db.scalar(
        select(Media).where(Media.id == media_id, Media.agency_id == user.id)
    )
    if not media:
        raise CustomAppError(
            message="Mídia não encontrada",
            error_type=CustomErrorType.not_found,
        )

    previous_designer_id = media.designer_id
    if designer_data.designer_id is None:
        media.designer_id = None
    else:
        designer = await db.scalar(
            select(Designer).where(
                Designer.id == designer_data.designer_id,
                Designer.agency_id == media.agency_id,
            )
        )
        if not designer:
            raise CustomAppError(
                message="Designer inválido ou não vinculado à agência da mídia",
                error_type=CustomErrorType.bad_request,
            )
        media.designer_id = designer.id

    await record_audit(
        db,
        user=user,
        action="authorship_change",
        resource_type="media",
        resource_id=media.id,
        resource_name=media.alias,
        message=(
            f"{user.name} alterou a autoria da mídia '{media.alias}' "
            f"de '{previous_designer_id}' para '{media.designer_id}'."
        ),
    )
    await db.commit()
    return media


async def get_media_library(
    db: AsyncSession,
    user: User,
) -> list[Media]:
    if user.type == UserType.agency:
        agency_id = user.id
    elif user.type == UserType.writer:
        agency_id = user.writer.agency_id if user.writer else None
    elif user.type == UserType.designer:
        agency_id = user.designer.agency_id if user.designer else None
    else:
        return []

    if not agency_id:
        return []

    result = await db.scalars(
        select(Media)
        .where(Media.agency_id == agency_id)
        .order_by(Media.created_at.desc())
    )
    return list(result.all())


async def get_media_for_view(
    db: AsyncSession,
    media_id,
    user: User,
) -> Media:
    media = await db.scalar(select(Media).where(Media.id == media_id))
    if not media:
        raise CustomAppError(
            message="Mídia não encontrada",
            error_type=CustomErrorType.not_found,
        )

    authorized = False
    if user.type == UserType.agency:
        authorized = media.agency_id == user.id
    elif user.type == UserType.writer:
        authorized = bool(user.writer and user.writer.agency_id == media.agency_id)
    elif user.type == UserType.designer:
        authorized = bool(user.designer and user.designer.agency_id == media.agency_id)
    elif user.type == UserType.client:
        authorized = (
            await db.scalar(
                select(PostMedia.id)
                .join(PostMedia.post)
                .where(
                    PostMedia.media_id == media.id,
                    Post.client_id == user.id,
                    Post.status != PostStatus.draft,
                )
                .limit(1)
            )
            is not None
        )

    if not authorized:
        raise CustomAppError(
            message="Você não tem permissão para visualizar esta mídia",
            error_type=CustomErrorType.forbidden,
        )

    return media


def get_media_path(filename: str) -> Path:
    root = LOCAL_STORAGE_PATH.resolve()
    path = (root / filename).resolve()
    if path.parent != root:
        raise CustomAppError(
            message="Caminho de mídia inválido",
            error_type=CustomErrorType.internal_server_error,
        )
    return path


async def update_media(
    db: AsyncSession,
    user: User,
    media_id,
    media_data: MediaUpdate,
) -> Media:
    media = await db.scalar(select(Media).where(Media.id == media_id))
    if not media:
        raise CustomAppError(
            message="Mídia não encontrada",
            error_type=CustomErrorType.not_found,
        )

    if user.type == UserType.agency:
        authorized = media.agency_id == user.id
    else:
        authorized = user.type == UserType.designer and media.designer_id == user.id
    if not authorized:
        raise CustomAppError(
            message="Apenas o Designer criador ou a Agência pode editar a mídia",
            error_type=CustomErrorType.forbidden,
        )

    previous_alias = media.alias
    media.alias = media_data.alias
    await record_audit(
        db,
        user=user,
        action="update",
        resource_type="media",
        resource_id=media.id,
        resource_name=media.alias,
        message=(
            f"{user.name} alterou o alias da mídia '{previous_alias}' "
            f"para '{media.alias}'."
        ),
    )
    await db.commit()
    return media


async def delete_media(
    db: AsyncSession,
    user: User,
    media_id,
) -> None:
    media = await db.scalar(
        select(Media)
        .options(selectinload(Media.post_medias).selectinload(PostMedia.post))
        .where(Media.id == media_id)
    )
    if not media:
        raise CustomAppError(
            message="Mídia não encontrada",
            error_type=CustomErrorType.not_found,
        )

    if user.type == UserType.agency:
        authorized = media.agency_id == user.id
    else:
        authorized = user.type == UserType.designer and media.designer_id == user.id
    if not authorized:
        raise CustomAppError(
            message="Apenas o Designer criador ou a Agência pode excluir a mídia",
            error_type=CustomErrorType.forbidden,
        )

    posts = [post_media.post for post_media in media.post_medias]
    if any(
        post.status in (PostStatus.approved, PostStatus.denied, PostStatus.published)
        for post in posts
    ):
        raise CustomAppError(
            message="A mídia não pode ser excluída porque está vinculada a um post final",
            error_type=CustomErrorType.conflict,
        )

    for post in posts:
        post.status = PostStatus.draft

    filename = media.filename
    await record_audit(
        db,
        user=user,
        action="delete",
        resource_type="media",
        resource_id=media.id,
        resource_name=media.alias,
        message=f"{user.name} excluiu a mídia '{media.alias}'.",
        agency_id=media.agency_id,
    )
    for post_media in media.post_medias:
        await db.delete(post_media)
    await db.delete(media)
    await db.commit()

    path = get_media_path(filename)
    if path.exists():
        try:
            await asyncio.to_thread(path.unlink)
        except OSError as exc:
            raise CustomAppError(
                message="Mídia removida do banco, mas não foi possível remover o arquivo",
                error_type=CustomErrorType.internal_server_error,
            ) from exc
