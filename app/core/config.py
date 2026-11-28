from os import getenv
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


def get_env(name: str, *, required: bool = False) -> str | None:
    value = getenv(name)
    if required and not value:
        raise RuntimeError(f"{name} variável de ambiente {name} não foi encontrada.")
    return value


API_KEY_ENV_NAME = "API_KEY"
API_KEY_HEADER_NAME = "X-API-KEY"
JWT_SECRET_KEY = get_env("SECRET_KEY", required=True)
JWT_ALGORITHM = "HS256"
JWT_EXPIRES_MINUTES = 60 * 36  # 36 horas
LOGIN_MAX_ATTEMPTS = 5
LOGIN_WINDOW_MINUTES = 15
LOGIN_BLOCK_MINUTES = 15
# Convites: código curto para digitar, sem caracteres ambíguos (0/O, 1/I/L)
INVITE_TOKEN_ALPHABET = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"
INVITE_TOKEN_LENGTH = 6
INVITE_TOKEN_TTL_DAYS = 7
# Tentativas de vínculo com token inválido, por usuário
INVITE_LINK_MAX_ATTEMPTS = 5
INVITE_LINK_WINDOW_MINUTES = 10
INVITE_LINK_BLOCK_MINUTES = 10
LOCAL_STORAGE_PATH = Path(get_env("LOCAL_STORAGE", required=True))
MAX_FILE_BYTES = 200 * 1024 * 1024  # 200mb
CHUNKS_PER_READ = 10 * 1024 * 1024  # 10mb
ALLOWED_FILE_TYPES = {
    "image/jpeg": ".jpeg",
    "image/png": ".png",
    "video/mp4": ".mp4",
}

if not LOCAL_STORAGE_PATH.exists():
    LOCAL_STORAGE_PATH.mkdir(parents=True)
