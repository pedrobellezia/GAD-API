from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import contains_eager

from app.models import Writer, Agency, User
from app.schemas import WriterCreate, WriterFilter


async def get_writers(db: AsyncSession, filters: WriterFilter) -> list[Writer]:
    query = (
        select(Writer)
        .join(Writer.user)
        .join(Writer.agency)
        .options(
            contains_eager(Writer.user),
            contains_eager(Writer.agency),
        )
    )

    if filters.id:
        query = query.where(Writer.id == filters.id)

    if filters.user_name:
        query = query.where(User.name.ilike(f"%{filters.user_name}%"))

    if filters.agency_cnpj:
        query = query.where(Agency.cnpj == filters.agency_cnpj)

    if filters.agency_name:
        query = query.where(Agency.name.ilike(f"%{filters.agency_name}%"))

    query = query.offset(filters.skip).limit(filters.limit)

    result = await db.execute(query)
    return list(result.scalars().unique().all())


async def create_writer(db: AsyncSession, writer_data: WriterCreate):
    new_writer = Writer(**writer_data.model_dump())
    db.add(new_writer)
    await db.commit()
    await db.refresh(new_writer)
    return new_writer
