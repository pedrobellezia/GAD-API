from datetime import UTC, datetime
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import pswd_hasher
from app.models import Agency, Client, Designer, User, UserType, Writer
from app.schemas import UserCreate, UserFilter
from app.services.audit_log import record_audit


async def get_users(db: AsyncSession, filters: UserFilter) -> list[User]:
    query = select(User)
    query = filters.apply_filters(query)

    result = await db.execute(query)
    return list(result.scalars().all())


async def create_user(db: AsyncSession, user_data: UserCreate, user_type: UserType):
    new_user = User(**user_data.model_dump(exclude={"pswd"}))
    new_user.pswd = pswd_hasher.hash(user_data.pswd)
    new_user.type = user_type
    db.add(new_user)

    await db.refresh(new_user)
    return new_user


async def load_user(db: AsyncSession, user_id: UUID) -> User | None:
    user = await db.scalar(select(User).where(User.id == user_id))
    if user:
        await db.refresh(user, [user.type.value])
    return user


async def resolve_profile(user: User) -> Client | Writer | Designer | Agency | None:
    match user.type:
        case UserType.client:
            return user.client
        case UserType.writer:
            return user.writer
        case UserType.designer:
            return user.designer
        case UserType.agency:
            return user.agency
        case _:
            return None


async def get_profile(
    db: AsyncSession, *, user_id: UUID
) -> Client | Writer | Designer | Agency | None:
    user = await load_user(db, user_id)
    return None if not user else await resolve_profile(user)


async def deactivate_user(db: AsyncSession, user: User) -> None:
    if user.type == UserType.agency:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="A desativação de agências não está disponível",
        )

    if user.deleted_at is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A conta já está desativada",
        )

    profile = await resolve_profile(user)
    agency_id = profile.agency_id if profile else None

    if profile and agency_id:
        from app.services.agency import unlink_member

        await unlink_member(db=db, member=profile, actor=user, commit=False)

    user.deleted_at = datetime.now(UTC)

    await record_audit(
        db,
        user=user,
        action="deactivate",
        resource_type="user",
        resource_id=user.id,
        resource_name=user.name,
        agency_id=agency_id,
        message=f"{user.name} desativou a própria conta.",
    )
    await db.commit()
