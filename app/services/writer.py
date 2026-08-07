from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import contains_eager, aliased, selectinload

from app.core import pswd_hasher
from app.models import Writer, Agency, User, UserType
from app.schemas import WriterCreate, WriterFilter


async def get_writers(db: AsyncSession, filters: WriterFilter) -> list[Writer]:
    agency_user = aliased(User)

    query = (
        select(Writer)
        .join(Writer.user)
        .outerjoin(Writer.agency)
        .outerjoin(agency_user, Agency.user)  # type: ignore
        .options(
            contains_eager(Writer.user),
            contains_eager(Writer.agency).contains_eager(
                Agency.user,
                alias=agency_user,  # type: ignore
            ),
        )
    )

    query = filters.apply_filters(query, agency_user=agency_user)

    result = await db.execute(query)
    return list(result.scalars().unique().all())


async def create_writer(db: AsyncSession, writer_data: WriterCreate) -> None:
    new_user = User(**writer_data.user.model_dump(exclude={"pswd"}))
    new_user.pswd = pswd_hasher.hash(writer_data.user.pswd)
    new_user.type = UserType.writer
    db.add(new_user)

    new_writer = Writer(id=new_user.id, agency_id=writer_data.agency_id)
    db.add(new_writer)


async def get_writer_me(db: AsyncSession, user_id) -> Writer:
    writer = await db.scalar(
        select(Writer)
        .options(
            selectinload(Writer.user),
            selectinload(Writer.agency).selectinload(Agency.user),
        )
        .where(Writer.id == user_id)
    )
    return writer
