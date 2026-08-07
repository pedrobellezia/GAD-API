from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas import LoginPayload, RegisterPayload, DetailsResponse, LoginResponse
from app.services import login, register

router = APIRouter()


@router.post(
    path="/login", status_code=status.HTTP_200_OK, response_model=LoginResponse
)
async def route_login(login_payload: LoginPayload, db: AsyncSession = Depends(get_db)):
    jwt_token = await login(db, login_payload)
    return {"token": jwt_token}


@router.post(
    path="/register",
    status_code=status.HTTP_201_CREATED,
    response_model=DetailsResponse,
)
async def route_register(
    register_payload: RegisterPayload, db: AsyncSession = Depends(get_db)
):
    await register(db, register_payload)
    await db.commit()
    return {"details": "Usuario criado com sucesso"}
