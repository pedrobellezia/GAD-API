from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models import Agency
from app.schemas import AgencyCreate, AgencyFilter


async def get_agencies(db: AsyncSession, filters: AgencyFilter) -> list[Agency]:
    query = select(Agency).options(
        joinedload(Agency.clients), joinedload(Agency.writers)
    )

    if filters.cnpj:
        query = query.where(Agency.cnpj == filters.cnpj)

    if filters.name:
        query = query.where(Agency.name.ilike(f"%{filters.name}%"))

    query = query.offset(filters.skip).limit(filters.limit)

    result = await db.execute(query)
    return list(result.scalars().unique().all())


async def create_agency(db: AsyncSession, agency_data: AgencyCreate) -> Agency:
    new_agency = Agency(**agency_data.model_dump())
    db.add(new_agency)
    await db.commit()
    await db.refresh(new_agency)
    return new_agency
