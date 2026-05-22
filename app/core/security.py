from datetime import datetime, timezone, timedelta
from uuid import UUID

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyHeader, HTTPBearer
from pwdlib import PasswordHash
from pydantic import ValidationError
from magic import Magic

from app.core import (
    API_KEY_ENV_NAME,
    API_KEY_HEADER_NAME,
    JWT_ALGORITHM,
    JWT_EXPIRES_MINUTES,
    JWT_SECRET_KEY,
    get_env,
)
from app.schemas import JwtPayload

api_key_header = APIKeyHeader(name=API_KEY_HEADER_NAME, auto_error=False)
pswd_hasher = PasswordHash.recommended()
bearer_scheme = HTTPBearer(auto_error=False)
mime_detector = Magic(mime=True)


def get_api_key(api_key: str | None = Depends(api_key_header)) -> str:
    expected_key = get_env(API_KEY_ENV_NAME, required=True)

    if not api_key or api_key != expected_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Chave de API inválida ou ausente",
        )

    return api_key


def create_token(user_id: UUID) -> str:
    payload = {
        "sub": str(user_id),
        "exp": datetime.now(timezone.utc) + timedelta(minutes=JWT_EXPIRES_MINUTES),
    }

    token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return token


def decode_token(token: str) -> JwtPayload:
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return JwtPayload.model_validate(payload)

    except jwt.ExpiredSignatureError:
        raise HTTPException(401, "Token JWT expirado")

    except (jwt.InvalidTokenError, ValidationError):
        raise HTTPException(401, "Token JWT inválido")
