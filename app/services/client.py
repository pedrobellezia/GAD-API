from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import contains_eager, aliased, selectinload

from app.core import pswd_hasher
from app.models import Client, Agency, User, UserType
from app.schemas import ClientCreate, ClientFilter


async def get_clients(db: AsyncSession, filters: ClientFilter) -> list[Client]:
    agency_user = aliased(User)

    query = (
        select(Client)
        .join(Client.user)
        .outerjoin(Client.agency)
        .outerjoin(agency_user, Agency.user)
        .options(
            contains_eager(Client.user),
            contains_eager(Client.agency).contains_eager(
                Agency.user,
                alias=agency_user,
            ),
        )
    )

    query = filters.apply_filters(query, agency_user=agency_user)

    result = await db.execute(query)
    return list(result.scalars().unique().all())


async def create_client(db: AsyncSession, client_data: ClientCreate) -> None:
    new_user = User(**client_data.user.model_dump(exclude={"pswd"}))
    new_user.pswd = pswd_hasher.hash(client_data.user.pswd)
    new_user.type = UserType.client
    db.add(new_user)

    new_client = Client(id=new_user.id, agency_id=client_data.agency_id)
    db.add(new_client)


async def get_client_me(db: AsyncSession, user_id) -> Client:
    client = await db.scalar(
        select(Client)
        .options(
            selectinload(Client.user),
            selectinload(Client.agency).selectinload(Agency.user),
        )
        .where(Client.id == user_id)
    )

    return client
