from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    Request,
    UploadFile,
    status,
)
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_profile, get_current_user
from app.exceptions import CustomAppError, CustomErrorType
from app.models import Designer, Media, MediaType, User, UserType
from app.schemas import (
    DetailsResponse,
    MediaDesignerUpdate,
    MediaRead,
    MediaUpdate,
)
from app.services.media import (
    delete_media,
    get_media_for_view,
    get_media_library,
    get_media_path,
    update_media,
    update_media_designer,
    upload_medias,
)
from app.services.thumbnail import ensure_thumbnail

router = APIRouter()


# O conteúdo de uma mídia nunca muda depois do upload; "private" evita cache em proxies
MEDIA_CACHE_HEADERS = {"Cache-Control": "private, max-age=86400"}


def media_read_response(media: Media, request: Request) -> MediaRead:
    response = MediaRead.model_validate(media)
    return response.model_copy(
        update={
            "url": str(request.url_for("serve_media_file", media_id=media.id)),
            "thumbnail_url": str(
                request.url_for("serve_media_thumbnail", media_id=media.id)
            ),
        }
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
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user(UserType.agency)),
):
    media = await update_media_designer(
        db=db,
        user=user,
        media_id=media_id,
        designer_data=designer_data,
    )
    return media_read_response(media, request)


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
        headers=MEDIA_CACHE_HEADERS,
    )


@router.get(
    path="/{media_id}/thumbnail",
    name="serve_media_thumbnail",
    response_class=FileResponse,
    summary="Visualizar miniatura da mídia",
)
async def route_serve_media_thumbnail(
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
    thumbnail = await ensure_thumbnail(media)
    if thumbnail:
        return FileResponse(
            path=thumbnail, media_type="image/webp", headers=MEDIA_CACHE_HEADERS
        )

    # Sem miniatura (falha na geração): imagem cai para o original; vídeo não tem fallback
    path = get_media_path(media.filename)
    if media.media_type == MediaType.image and path.is_file():
        return FileResponse(
            path=path, media_type=media.mime_type, headers=MEDIA_CACHE_HEADERS
        )
    raise CustomAppError(
        message="Miniatura indisponível",
        error_type=CustomErrorType.not_found,
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
    file_errors = await upload_medias(
        db=db,
        user=user,
        member=member,
        files=files,
        aliases=aliases,
    )
    return {
        "details": "Upload concluído",
        "errors": file_errors,
    }
