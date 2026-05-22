from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core import pswd_hasher
from app.models import User, Client, Writer, Designer
from app.schemas import UserCreate, UserFilter


async def get_users(db: AsyncSession, filters: UserFilter) -> list[User]:
    query = select(User)

    if filters.id:
        query = query.where(User.id == filters.id)
    if filters.name:
        query = query.where(User.name.ilike(f"%{filters.name}%"))
    if filters.email:
        query = query.where(User.email == filters.email)
    if filters.type:
        query = query.where(User.type == filters.type)

    query = query.offset(filters.skip).limit(filters.limit)

    result = await db.execute(query)
    return list(result.scalars().all())


async def create_user(db: AsyncSession, user_data: UserCreate):
    new_user = User(**user_data.model_dump(exclude={"pswd"}))
    new_user.pswd = pswd_hasher.hash(user_data.pswd)
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user


async def get_profile(
    db: AsyncSession, *, user_id: UUID
) -> Client | Writer | Designer | None:
    user = await db.scalar(
        select(User)
        .options(
            selectinload(User.client),
            selectinload(User.writer),
            selectinload(User.designer),
        )
        .where(User.id == user_id)
    )
    return None if not user else user.client or user.writer or user.designer
