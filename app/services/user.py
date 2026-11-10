import asyncio
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import set_committed_value

from app.core import pswd_hasher
from app.models import Agency, Client, Designer, User, UserType, Writer
from app.schemas import UserCreate, UserFilter
from app.services.audit_log import record_audit
from app.services.media import get_media_path, store_media_file, validate_media_file


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
        profile = getattr(user, user.type.value, None)
        if profile is not None:
            set_committed_value(profile, "user", user)
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
    await db.execute(
        text("SELECT soft_delete_user(:user_id)"),
        {"user_id": user.id},
    )
    await db.commit()


async def update_profile(
    db: AsyncSession, user: User, name: str | None, email: str | None
):
    if name is None and email is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Informe ao menos um campo para atualizar",
        )

    if email is not None:
        email = email.strip().lower()

    if email is not None and email != user.email:
        existing = await db.scalar(select(User).where(User.email == email))
        if existing and existing.id != user.id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="O email informado já está em uso",
            )

    previous_name = user.name
    previous_email = user.email
    if name is not None:
        user.name = name
    if email is not None:
        user.email = email

    try:
        if user.name != previous_name:
            await record_audit(
                db,
                user=user,
                action="update",
                resource_type="user",
                resource_id=user.id,
                resource_name=user.name,
                message=(
                    f"{user.name} alterou o nome de '{previous_name}' para '{user.name}'."
                ),
            )
        if user.email != previous_email:
            await record_audit(
                db,
                user=user,
                action="update",
                resource_type="user",
                resource_id=user.id,
                resource_name=user.name,
                message=(
                    f"{user.name} alterou o email de '{previous_email}' para '{user.email}'."
                ),
            )
        await db.commit()
    except IntegrityError as err:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="O email informado já está em uso",
        ) from err
    return user


async def update_avatar(db: AsyncSession, user: User, file) -> None:
    file_info = await validate_media_file(file)
    if file_info.media_type.value != "image":
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="O avatar deve ser uma imagem JPEG ou PNG",
        )

    filename, _ = await store_media_file(file, file_info.extension)
    previous_filename = user.avatar
    user.avatar = filename
    try:
        await record_audit(
            db,
            user=user,
            action="update",
            resource_type="user",
            resource_id=user.id,
            resource_name=user.name,
            message=f"{user.name} atualizou o avatar.",
        )
        await db.commit()
    except Exception:
        await db.rollback()
        path = get_media_path(filename)
        if path.exists():
            await asyncio.to_thread(path.unlink)
        raise

    if previous_filename:
        previous_path = get_media_path(previous_filename)
        if previous_path.exists():
            await asyncio.to_thread(previous_path.unlink)


async def remove_avatar(db: AsyncSession, user: User) -> None:
    previous_filename = user.avatar
    if not previous_filename:
        return
    user.avatar = None
    await record_audit(
        db,
        user=user,
        action="delete",
        resource_type="user",
        resource_id=user.id,
        resource_name=user.name,
        message=f"{user.name} removeu o avatar.",
    )
    await db.commit()
    path = get_media_path(previous_filename)
    if path.exists():
        await asyncio.to_thread(path.unlink)
