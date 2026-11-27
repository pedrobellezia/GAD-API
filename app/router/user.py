import hashlib
from uuid import UUID

from fastapi import APIRouter, Depends, Request
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.exceptions import CustomAppError, CustomErrorType
from app.models import User
from app.schemas import UserSummary
from app.services.media import get_media_path

router = APIRouter()


def user_summary_response(user: User | None, request: Request) -> UserSummary | None:
    if user is None:
        return None
    avatar_url = None
    if user.avatar:
        version = hashlib.sha256(user.avatar.encode()).hexdigest()[:12]
        avatar_url = f"{request.app.url_path_for('serve_user_avatar', user_id=user.id)}?v={version}"
    return UserSummary(
        id=user.id,
        name=user.name,
        type=user.type,
        avatar_url=avatar_url,
    )


@router.get(
    path="/{user_id}/avatar",
    name="serve_user_avatar",
    response_class=FileResponse,
    summary="Visualizar foto de perfil de um usuário",
)
async def route_serve_user_avatar(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user()),
):
    target = await db.scalar(select(User).where(User.id == user_id))
    if not target or not target.avatar:
        raise CustomAppError(
            message="Avatar não encontrado",
            error_type=CustomErrorType.not_found,
        )
    path = get_media_path(target.avatar)
    if not path.is_file():
        raise CustomAppError(
            message="Avatar não encontrado",
            error_type=CustomErrorType.not_found,
        )
    return FileResponse(path=path)
