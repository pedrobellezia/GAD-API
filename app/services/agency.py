from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import contains_eager, selectinload

from app.core import pswd_hasher
from app.models import Agency, User, UserType
from app.schemas import AgencyCreate, AgencyFilter
from app.services.invite_token import create_invite_tokens


async def get_agencies(db: AsyncSession, filters: AgencyFilter) -> list[Agency]:
    query = select(Agency).join(Agency.user).options(contains_eager(Agency.user))

    if filters.id:
        query = query.where(Agency.id == filters.id)

    if filters.cnpj:
        query = query.where(Agency.cnpj == filters.cnpj)

    if filters.user_email:
        query = query.where(User.email == filters.user_email)

    if filters.user_name:
        query = query.where(User.name.ilike(f"%{filters.user_name}%"))

    query = query.offset(filters.skip).limit(filters.limit)

    result = await db.execute(query)
    return list(result.scalars().unique().all())


async def create_agency(db: AsyncSession, agency_data: AgencyCreate) -> None:
    async with db.begin():
        new_user = User(**agency_data.user.model_dump(exclude={"pswd"}))
        new_user.pswd = pswd_hasher.hash(agency_data.user.pswd)
        new_user.type = UserType.agency
        db.add(new_user)
        await db.flush()

        new_agency = Agency(id=new_user.id, cnpj=agency_data.cnpj)
        db.add(new_agency)
        await db.flush()

        await create_invite_tokens(db, agency_id=new_agency.id, quantity=10)


async def get_agency_me(db: AsyncSession, user_id) -> Agency:
    agency = await db.scalar(
        select(Agency).options(selectinload(Agency.user)).where(Agency.id == user_id)
    )
    return agency


async def get_my_clients(db: AsyncSession, agency_id) -> list[User]:
    result = await db.execute(
        select(User).join(User.client).where(User.client.has(agency_id=agency_id))
    )
    return list(result.scalars().all())


async def get_my_writers(db: AsyncSession, agency_id) -> list[User]:
    result = await db.execute(
        select(User).join(User.writer).where(User.writer.has(agency_id=agency_id))
    )
    return list(result.scalars().all())


async def get_my_designers(db: AsyncSession, agency_id) -> list[User]:
    result = await db.execute(
        select(User).join(User.designer).where(User.designer.has(agency_id=agency_id))
    )
    return list(result.scalars().all())
