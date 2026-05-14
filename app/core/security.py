from os import getenv

from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyHeader
from pwdlib import PasswordHash

API_KEY_ENV_NAME = "API_KEY"
api_key_header = APIKeyHeader(name="X-API-KEY", auto_error=False)


def get_api_key(api_key: str | None = Depends(api_key_header)) -> str:
    expected_key = getenv(API_KEY_ENV_NAME)
    if not expected_key:
        raise RuntimeError(f"{API_KEY_ENV_NAME} environment variable is not set")

    if not api_key or api_key != expected_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Chave de API inválida ou ausente",
        )

    return api_key


pswd_hasher = PasswordHash.recommended()
