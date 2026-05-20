from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas import LoginPayload, RegisterPayload, DetailsResponse, LoginResponse
from app.services import login, register

router = APIRouter()


@router.post(path="/login", status_code=200, response_model=LoginResponse)
async def route_login(login_payload: LoginPayload, db: AsyncSession = Depends(get_db)):
    jwt_token = await login(db, login_payload)
    return {"token": jwt_token}


@router.post(path="/register", status_code=201, response_model=DetailsResponse)
async def route_register(
    register_payload: RegisterPayload, db: AsyncSession = Depends(get_db)
):
    await register(db, register_payload)
    return {"details": "Usuario criado com sucesso"}
