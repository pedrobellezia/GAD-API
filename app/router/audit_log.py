from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models import User, UserType
from app.schemas import AuditLogRead
from app.services.audit_log import get_audit_logs

router = APIRouter()


@router.get(
    "",
    response_model=list[AuditLogRead],
    status_code=status.HTTP_200_OK,
    summary="Listar histórico de auditoria",
)
async def route_get_audit_logs(
    action: str | None = Query(default=None, min_length=1),
    resource_type: str | None = Query(default=None, min_length=1),
    resource_id: UUID | None = Query(default=None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user(UserType.agency)),
):
    return await get_audit_logs(
        db=db,
        user=user,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        skip=skip,
        limit=limit,
    )
