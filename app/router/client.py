from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import get_db
from app.schemas import ClientCreate, ClientRead, ClientFilter
from app.services import create_client, get_clients

router = APIRouter()


@router.post("/", response_model=ClientRead)
async def route_post_client(
    client_data: ClientCreate, db: AsyncSession = Depends(get_db)
):
    new_client = await create_client(db, client_data)
    return new_client


@router.get("/", response_model=list[ClientRead] | None)
async def route_get_clients(
    client_data: ClientFilter, db: AsyncSession = Depends(get_db)
):
    new_client = await get_clients(db, client_data)
    return new_client if new_client else None


@router.get("/{client_id}", response_model=ClientRead | None)
async def route_get_client_by_id(client_id: UUID, db: AsyncSession = Depends(get_db)):
    new_client = await get_clients(db, ClientFilter(id=client_id).model_dump())
    return new_client[0] if new_client else None
