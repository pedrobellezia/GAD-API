from .agency import router as agency_router
from .client import router as client_router
from .user import router as user_router
from .writer import router as writer_router

__all__ = [
    "agency_router",
    "client_router",
    "user_router",
    "writer_router",
]
