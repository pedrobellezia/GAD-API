from os import getenv

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError, ResponseValidationError

from app.handlers import request_validation_handler, response_validation_handler
from app.router import agency_router, client_router, user_router, writer_router

app = FastAPI(title="Fenix API", redirect_slashes=False)

app.include_router(agency_router, prefix="/agency", tags=["agency"])
app.include_router(client_router, prefix="/client", tags=["client"])
app.include_router(user_router, prefix="/user", tags=["user"])
app.include_router(writer_router, prefix="/writer", tags=["writer"])

app.add_exception_handler(RequestValidationError, request_validation_handler)
app.add_exception_handler(ResponseValidationError, response_validation_handler)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.app:app",
        host=getenv("HOST"),
        port=int(getenv("PORT")),
        reload=True,
    )
