from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import get_db
from app.schemas import WriterCreate, WriterRead, WriterFilter
from app.services import create_writer, get_writers

router = APIRouter()


@router.post(path="", status_code=202)
async def route_post_writer(
    writer_data: WriterCreate, db: AsyncSession = Depends(get_db)
):
    await create_writer(db, writer_data)


@router.get(path="", response_model=list[WriterRead] | None, status_code=200)
async def route_get_writers(
    writer_data: WriterFilter = Depends(), db: AsyncSession = Depends(get_db)
):
    new_writer = await get_writers(db, writer_data)
    return new_writer


@router.get("/{writer_id}", response_model=WriterRead | None, status_code=200)
async def route_get_writer_by_id(writer_id: UUID, db: AsyncSession = Depends(get_db)):
    new_writer = await get_writers(db, WriterFilter(id=writer_id))
    return new_writer[0] if new_writer else None
