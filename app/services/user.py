from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.core import pswd_hasher
from app.models import User
from app.schemas import UserCreate, UserFilter


async def get_users(db: AsyncSession, filters: UserFilter) -> list[User]:
    query = select(User).options(joinedload(User.client), joinedload(User.writer))

    if filters.name:
        query = query.where(User.username.ilike(f"%{filters.name}%"))
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
