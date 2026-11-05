import asyncio
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Request,
    UploadFile,
    status,
)
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import LOCAL_STORAGE_PATH
from app.core.database import get_db
from app.core.dependencies import get_current_profile, get_current_user
from app.exceptions import CustomAppError, CustomErrorType
from app.models import Designer, Media, User, UserType
from app.schemas import (
    DetailsResponse,
    MediaDesignerUpdate,
    MediaRead,
    MediaUpdate,
)
from app.services.audit_log import record_audit
from app.services.media import (
    delete_media,
    get_media_for_view,
    get_media_library,
    get_media_path,
    store_media_file,
    update_media,
    update_media_designer,
    validate_media_file,
)

router = APIRouter()


def media_read_response(media: Media, request: Request) -> MediaRead:
    response = MediaRead.model_validate(media)
    return response.model_copy(
        update={"url": str(request.url_for("serve_media_file", media_id=media.id))}
    )


@router.get(
    path="",
    status_code=status.HTTP_200_OK,
    response_model=list[MediaRead],
    summary="Listar mídias da agência",
)
async def route_get_medias(
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(
        get_current_user(UserType.agency, UserType.writer, UserType.designer)
    ),
):
    medias = await get_media_library(db=db, user=user)
    return [media_read_response(media, request) for media in medias]


@router.patch(
    path="/{media_id}/designer",
    status_code=status.HTTP_200_OK,
    response_model=MediaRead,
    summary="Alterar designer da mídia",
)
async def route_update_media_designer(
    media_id: UUID,
    designer_data: MediaDesignerUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user(UserType.agency)),
):
    return await update_media_designer(
        db=db,
        user=user,
        media_id=media_id,
        designer_data=designer_data,
    )


@router.patch(
    path="/{media_id}",
    status_code=status.HTTP_200_OK,
    response_model=MediaRead,
    summary="Editar alias da mídia",
)
async def route_update_media(
    media_id: UUID,
    media_data: MediaUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user(UserType.agency, UserType.designer)),
):
    media = await update_media(
        db=db,
        user=user,
        media_id=media_id,
        media_data=media_data,
    )
    return media_read_response(media, request)


@router.get(
    path="/{media_id}/file",
    name="serve_media_file",
    response_class=FileResponse,
    summary="Visualizar mídia protegida",
)
async def route_serve_media_file(
    media_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(
        get_current_user(
            UserType.agency,
            UserType.writer,
            UserType.designer,
            UserType.client,
        )
    ),
):
    media = await get_media_for_view(db=db, media_id=media_id, user=user)
    path = get_media_path(media.filename)
    if not path.is_file():
        raise CustomAppError(
            message="Arquivo da mídia não encontrado",
            error_type=CustomErrorType.not_found,
        )
    return FileResponse(
        path=path,
        media_type=media.mime_type,
        filename=media.filename,
    )


@router.delete(
    path="/{media_id}",
    status_code=status.HTTP_200_OK,
    response_model=DetailsResponse,
    summary="Excluir mídia",
)
async def route_delete_media(
    media_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user()),
):
    await delete_media(db=db, user=user, media_id=media_id)
    return {"details": "Mídia excluída com sucesso"}


@router.post(
    path="/upload",
    status_code=status.HTTP_201_CREATED,
    response_model=DetailsResponse,
)
async def route_upload_medias(
    files: list[UploadFile] = File(...),
    aliases: list[str] = Form(...),
    db: AsyncSession = Depends(get_db),
    member: Designer = Depends(get_current_profile(UserType.designer)),
    user: User = Depends(get_current_user(UserType.designer)),
):
    if len(aliases) != len(files):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="O número de aliases deve ser igual ao número de arquivos",
        )

    medias: list[Media] = []
    filename_list: list[str] = []
    file_errors: list[dict] = []

    try:
        for alias, file in zip(aliases, files, strict=True):
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
                        designer_id=member.id,
                        agency_id=member.agency_id,
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
            for media in medias:
                await record_audit(
                    db,
                    user=user,
                    action="create",
                    resource_type="media",
                    resource_id=media.id,
                    resource_name=media.alias,
                    message=f"{user.name} enviou a mídia '{media.alias}'.",
                    agency_id=member.agency_id,
                )

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
