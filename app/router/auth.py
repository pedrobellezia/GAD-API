from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import get_db
from app.schemas import LoginPayload, RegisterPayload
from app.services import login, register

router = APIRouter()


@router.post(path="/login")
async def route_login(login_payload: LoginPayload, db: AsyncSession = Depends(get_db)):
    # future jwt return
    return await login(db, login_payload)


@router.post(path="/register")
async def route_register(
    register_payload: RegisterPayload, db: AsyncSession = Depends(get_db)
):
    await register(db, register_payload)
