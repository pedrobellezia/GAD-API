from app.core import get_env

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError, ResponseValidationError
from sqlalchemy.exc import IntegrityError

from app.exceptions import (
    request_validation_handler,
    response_validation_handler,
    integrity_error_handler,
)
from app.router import agency_router, auth_router, me_router, media_router
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Fenix API")

app.include_router(agency_router, prefix="/agency", tags=["agency"])
app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(me_router, prefix="/me", tags=["me"])
app.include_router(media_router, prefix="/media", tags=["media"])

app.add_exception_handler(RequestValidationError, request_validation_handler)
app.add_exception_handler(ResponseValidationError, response_validation_handler)
app.add_exception_handler(IntegrityError, integrity_error_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.app:app",
        host=get_env("HOST"),
        port=int(get_env("PORT")),
        reload=True,
    )
