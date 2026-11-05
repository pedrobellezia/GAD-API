from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import CustomAppError, CustomErrorType
from app.models import AuditLog, User, UserType


def _agency_id(user: User) -> UUID | None:
    if user.type == UserType.agency:
        return user.id
    if user.type in (UserType.client, UserType.writer, UserType.designer):
        profile = getattr(user, user.type.value, None)
        return profile.agency_id if profile else None
    return None


async def record_audit(
    db: AsyncSession,
    *,
    user: User,
    action: str,
    resource_type: str,
    message: str,
    resource_id: UUID | None = None,
    resource_name: str | None = None,
    agency_id: UUID | None = None,
) -> AuditLog:
    audit_log = AuditLog(
        agency_id=agency_id if agency_id is not None else _agency_id(user),
        actor_id=user.id,
        actor_name=user.name,
        actor_email=user.email,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        resource_name=resource_name,
        message=message,
    )
    db.add(audit_log)
    await db.flush()
    return audit_log


async def get_audit_logs(
    db: AsyncSession,
    *,
    user: User,
    action: str | None = None,
    resource_type: str | None = None,
    skip: int = 0,
    limit: int = 100,
) -> list[AuditLog]:
    if user.type != UserType.agency:
        raise CustomAppError(
            message="Apenas a agência pode consultar o histórico",
            error_type=CustomErrorType.forbidden,
        )

    query = select(AuditLog).where(AuditLog.agency_id == user.id)
    if action:
        query = query.where(AuditLog.action == action)
    if resource_type:
        query = query.where(AuditLog.resource_type == resource_type)

    result = await db.scalars(
        query.order_by(AuditLog.created_at.desc()).offset(skip).limit(limit)
    )
    return list(result.all())
