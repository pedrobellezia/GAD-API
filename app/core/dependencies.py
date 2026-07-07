from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.security import bearer_scheme, decode_token
from app.models import User, UserType
from app.schemas import JwtPayload


async def get_jwt_payload(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> JwtPayload:
    if not credentials or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token JWT ausente",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return decode_token(credentials.credentials)


def get_current_user(*req_types: UserType):
    async def dependency(
        db: AsyncSession = Depends(get_db),
        payload: JwtPayload = Depends(get_jwt_payload),
    ) -> User:

        user_id = payload.sub

        user: User = await db.scalar(select(User).where(User.id == user_id))

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuario nao encontrado",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if req_types and user.type not in req_types:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Usuario nao autorizado para este recurso",
            )

        await db.refresh(user, [user.type.value])

        return user

    return dependency
