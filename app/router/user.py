from uuid import UUID

from fastapi import APIRouter
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import get_db
from app.schemas import UserCreate, UserRead, UserFilter
from app.services import (create_user, get_users)

router = APIRouter()


@router.post("/", response_model=UserRead)
async def route_post_user(user_data: UserCreate, db: AsyncSession = get_db()):
    new_user = await create_user(db, user_data)
    return new_user


@router.get("/", response_model=list[UserRead] | None)
async def route_get_users(user_data: UserFilter, db: AsyncSession = get_db()):
    new_user = await get_users(db, user_data)
    return new_user if new_user else None


@router.get("/{user_id}", response_model=UserRead | None)
async def route_get_user_by_id(user_id: UUID, db: AsyncSession = get_db()):
    new_user = await get_users(db, UserFilter(id=user_id).model_dump())
    return new_user[0] if new_user else None
