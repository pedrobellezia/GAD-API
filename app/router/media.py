import asyncio

from fastapi import APIRouter, Form, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import LOCAL_STORAGE_PATH
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models import Media, User, UserType
from app.schemas import DetailsResponse
from app.services.media import validate_media_file, store_media_file
from app.exceptions import CustomAppError

router = APIRouter()


@router.post(path="/upload", status_code=201, response_model=DetailsResponse)
async def route_upload_medias(
    files: list[UploadFile] = File(...),
    aliases: list[str] = Form(...),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user(UserType.designer)),
):
    if len(aliases) != len(files):
        raise HTTPException(
            status_code=400,
            detail="O número de aliases deve ser igual ao número de arquivos",
        )

    medias: list[Media] = []
    filename_list: list[str] = []
    file_errors: list[dict] = []

    try:
        for alias, file in zip(aliases, files):
            try:
                file_info = await validate_media_file(file)

                filename, size_bytes = await store_media_file(
                    file=file,
                    extension=file_info.extension,
                )
                filename_list.append(filename)

                medias.append(
                    Media(
                        alias=alias,
                        filename=filename,
                        media_type=file_info.media_type,
                        mime_type=file_info.mime_type,
                        size_bytes=size_bytes,
                        designer_id=user.id,
                    )
                )
            except CustomAppError as exc:
                file_errors.append(
                    {
                        "alias": alias,
                        "error_type": exc.error_type.name,
                        "message": exc.message,
                    }
                )

        if medias:
            db.add_all(medias)

        await db.commit()
        return {
            "details": "Upload concluído",
            "errors": file_errors or None,
        }

    except Exception:
        await db.rollback()
        for q in filename_list:
            file_path = LOCAL_STORAGE_PATH / q
            if file_path.exists():
                await asyncio.to_thread(file_path.unlink)

        raise
    finally:
        for file in files:
            await file.close()
