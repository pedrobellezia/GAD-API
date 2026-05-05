from fastapi import FastAPI

from app.router import agency_router, client_router, user_router, writer_router

app = FastAPI(title="Fenix API", redirect_slashes=False)

app.include_router(agency_router, prefix="/agency", tags=["agency"])
app.include_router(client_router, prefix="/client", tags=["client"])
app.include_router(user_router, prefix="/user", tags=["user"])
app.include_router(writer_router, prefix="/writer", tags=["writer"])
