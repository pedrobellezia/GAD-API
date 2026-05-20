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
LOCAL_STORAGE_PATH = Path(get_env("LOCAL_STORAGE", required=True))
MAX_FILE_BYTES = 200 * 1024 * 1024  # 200mb

if not LOCAL_STORAGE_PATH.exists():
    LOCAL_STORAGE_PATH.mkdir(parents=True)
