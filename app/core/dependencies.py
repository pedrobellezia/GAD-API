from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import bearer_scheme, decode_token
from app.models import Client, Designer, User, UserType, Writer, Agency
from app.schemas import JwtPayload
from app.services import resolve_profile, load_user


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

        user = await load_user(db, user_id)

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

        return user

    return dependency


def get_current_profile(*req_types: UserType):
    async def dependency(
        user: User = Depends(get_current_user(*req_types)),
    ) -> Client | Writer | Designer | Agency:
        member = await resolve_profile(user)
        if not member:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Perfil de usuario nao encontrado",
            )
        return member
    return dependency
