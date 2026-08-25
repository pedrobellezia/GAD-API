import asyncio
from pathlib import Path
from uuid import uuid4

import aiofiles
from fastapi import UploadFile
from pydantic import BaseModel

from app.core import (
    ALLOWED_FILE_TYPES,
    CHUNKS_PER_READ,
    LOCAL_STORAGE_PATH,
    MAX_FILE_BYTES,
    mime_detector,
)
from app.exceptions import CustomAppError, CustomErrorType
from app.models import MediaType


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
