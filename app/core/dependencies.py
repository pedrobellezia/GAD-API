from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.security import bearer_scheme, decode_token
from app.models import User, UserType


async def get_current_user(
    db: AsyncSession = Depends(get_db),
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> User:
    if not credentials or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token JWT ausente",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_token(credentials.credentials)
    user_id = payload.get("sub")

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token JWT invalido",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        user_uuid = UUID(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token JWT invalido",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = await db.scalar(
        select(User)
        .options(
            selectinload(User.client),
            selectinload(User.writer),
            selectinload(User.agency),
        )
        .where(User.id == user_uuid)
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario nao encontrado",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


def _require_user_type(user: User, expected_type: UserType) -> User:
    if user.type != expected_type:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario nao autorizado",
        )
    return user


async def get_current_client(user: User = Depends(get_current_user)) -> User:
    _require_user_type(user, UserType.client)
    if not user.client:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario nao possui perfil de cliente",
        )
    return user


async def get_current_writer(user: User = Depends(get_current_user)) -> User:
    _require_user_type(user, UserType.writer)
    if not user.writer:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario nao possui perfil de writer",
        )
    return user


async def get_current_agency(user: User = Depends(get_current_user)) -> User:
    _require_user_type(user, UserType.agency)
    if not user.agency:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario nao possui perfil de agencia",
        )
    return user
