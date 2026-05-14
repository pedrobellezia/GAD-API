from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import contains_eager, aliased

from app.core import pswd_hasher
from app.models import Client, Agency, User, UserType
from app.schemas import ClientCreate, ClientFilter


async def get_clients(db: AsyncSession, filters: ClientFilter) -> list[Client]:
    agency_user = aliased(User)

    query = (
        select(Client)
        .join(Client.user)
        .join(Client.agency)
        .join(agency_user, Agency.user)
        .options(
            contains_eager(Client.user),
            contains_eager(Client.agency).contains_eager(
                Agency.user,
                alias=agency_user,
            ),
        )
    )

    if filters.id:
        query = query.where(Client.id == filters.id)

    if filters.user_name:
        query = query.where(User.name.ilike(f"%{filters.user_name}%"))

    if filters.user_email:
        query = query.where(User.email == filters.user_email)

    if filters.agency_cnpj:
        query = query.where(Agency.cnpj == filters.agency_cnpj)

    if filters.agency_name:
        query = query.where(agency_user.name.ilike(f"%{filters.agency_name}%"))

    query = query.offset(filters.skip).limit(filters.limit)

    result = await db.execute(query)
    return list(result.scalars().unique().all())


async def create_client(db: AsyncSession, client_data: ClientCreate) -> None:
    async with db.begin_nested():
        new_user = User(**client_data.user.model_dump(exclude={"pswd"}))
        new_user.pswd = pswd_hasher.hash(client_data.user.pswd)
        new_user.type = UserType.client
        db.add(new_user)
        await db.flush()

        new_client = Client(id=new_user.id, agency_id=client_data.agency_id)
        db.add(new_client)

    await db.commit()
