from datetime import datetime, timezone, timedelta
from uuid import UUID

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyHeader
from pwdlib import PasswordHash

from app.core import (
    API_KEY_ENV_NAME,
    API_KEY_HEADER_NAME,
    JWT_ALGORITHM,
    JWT_EXPIRES_MINUTES,
    JWT_SECRET_KEY,
    get_env,
)

api_key_header = APIKeyHeader(name=API_KEY_HEADER_NAME, auto_error=False)
pswd_hasher = PasswordHash.recommended()


def get_api_key(api_key: str | None = Depends(api_key_header)) -> str:
    expected_key = get_env(API_KEY_ENV_NAME, required=True)

    if not api_key or api_key != expected_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Chave de API inválida ou ausente",
        )

    return api_key


def create_token(user_id: UUID, **extra_info):
    payload = {
        "sub": str(user_id),
        **extra_info,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=JWT_EXPIRES_MINUTES),
    }

    token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return token


def decode_token(token: str):
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload

    except jwt.ExpiredSignatureError:
        raise HTTPException(401, "Token expirado")

    except jwt.InvalidTokenError:
        raise HTTPException(401, "Token inválido")
