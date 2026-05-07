from os import getenv

from fastapi import FastAPI, Depends
from fastapi.exceptions import RequestValidationError, ResponseValidationError
from sqlalchemy.exc import IntegrityError

from app.core import get_api_key
from app.handlers import (
    request_validation_handler,
    response_validation_handler,
    integrity_error_handler,
)
from app.router import agency_router, client_router, user_router, writer_router

app = FastAPI(title="Fenix API", redirect_slashes=False, dependencies=[Depends(get_api_key)])

app.include_router(agency_router, prefix="/agency", tags=["agency"])
app.include_router(client_router, prefix="/client", tags=["client"])
app.include_router(user_router, prefix="/user", tags=["user"])
app.include_router(writer_router, prefix="/writer", tags=["writer"])

app.add_exception_handler(RequestValidationError, request_validation_handler)
app.add_exception_handler(ResponseValidationError, response_validation_handler)
app.add_exception_handler(IntegrityError, integrity_error_handler)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.app:app",
        host=getenv("HOST"),
        port=int(getenv("PORT")),
        reload=True,
    )
