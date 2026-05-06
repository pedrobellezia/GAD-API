from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import contains_eager

from app.models import Client, Agency, User
from app.schemas import ClientCreate, ClientFilter


async def get_clients(db: AsyncSession, filters: ClientFilter) -> list[Client]:
    query = (
        select(Client)
        .join(Client.user)
        .join(Client.agency)
        .options(
            contains_eager(Client.user),
            contains_eager(Client.agency),
        )
    )

    if filters.user_name:
        query = query.where(User.name.ilike(f"%{filters.user_name}%"))

    if filters.agency_cnpj:
        query = query.where(Agency.cnpj == filters.agency_cnpj)

    if filters.agency_name:
        query = query.where(Agency.name.ilike(f"%{filters.agency_name}%"))

    query = query.offset(filters.skip).limit(filters.limit)

    result = await db.execute(query)
    return list(result.scalars().unique().all())


async def create_client(db: AsyncSession, client_data: ClientCreate) -> Client:
    new_client = Client(**client_data.model_dump())
    db.add(new_client)
    await db.commit()
    await db.refresh(new_client)
    return new_client
