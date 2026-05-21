from uuid import UUID

from app.utils.types import Member
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
            selectinload(User.designer),
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


async def get_current_member(
    user: User = Depends(get_current_user),
) -> Member:
    if user.agency:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Agencias nao tem acesso a este recurso",
        )

    member = user.client or user.writer or user.designer

    if not member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario nao tem perfil de cliente, escritor ou designer",
        )

    return member


async def get_current_agency(user: User = Depends(get_current_user)) -> User:
    if user.type != UserType.agency:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario nao autorizado",
        )

    if not user.agency:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario nao possui perfil de agencia",
        )
    return user
