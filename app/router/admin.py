from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas import (
    ClientCreate,
    ClientRead,
    ClientFilter,
    AgencyRead,
    WriterRead,
    WriterCreate,
    WriterFilter,
    AgencyCreate,
    AgencyFilter,
    UserCreate,
    UserRead,
    UserFilter,
)
from app.services import (
    create_agency,
    get_agencies,
    create_client,
    get_clients,
    create_writer,
    get_writers,
    create_user,
    get_users,
)

router = APIRouter()


@router.post(path="/user", status_code=202)
async def route_post_user(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    await create_user(db, user_data)


@router.get(path="/user", response_model=list[UserRead] | None, status_code=200)
async def route_get_users(
    user_data: UserFilter = Depends(), db: AsyncSession = Depends(get_db)
):
    new_user = await get_users(db, user_data)
    return new_user


@router.get("/user/{user_id}", response_model=UserRead | None, status_code=200)
async def route_get_user_by_id(user_id: UUID, db: AsyncSession = Depends(get_db)):
    new_user = await get_users(db, UserFilter(id=user_id))
    return new_user[0] if new_user else None


@router.post(path="/client", status_code=202)
async def route_post_client(
    client_data: ClientCreate, db: AsyncSession = Depends(get_db)
):
    await create_client(db, client_data)


@router.get(path="/client", response_model=list[ClientRead] | None, status_code=200)
async def route_get_clients(
    client_data: ClientFilter = Depends(), db: AsyncSession = Depends(get_db)
):
    new_client = await get_clients(db, client_data)
    return new_client


@router.get("/client/{client_id}", response_model=ClientRead | None, status_code=200)
async def route_get_client_by_id(client_id: UUID, db: AsyncSession = Depends(get_db)):
    new_client = await get_clients(db, ClientFilter(id=client_id))
    return new_client[0] if new_client else None


@router.post(path="/agency", status_code=202)
async def route_post_agency(
    agency_data: AgencyCreate, db: AsyncSession = Depends(get_db)
):
    await create_agency(db, agency_data)


@router.get(path="/agency", response_model=list[AgencyRead] | None, status_code=200)
async def route_get_agencies(
    agency_data: AgencyFilter = Depends(), db: AsyncSession = Depends(get_db)
):
    new_agency = await get_agencies(db, agency_data)
    return new_agency


@router.get("/agency/{agency_id}", response_model=AgencyRead | None, status_code=200)
async def route_get_agency_by_id(agency_id: UUID, db: AsyncSession = Depends(get_db)):
    new_agency = await get_agencies(db, AgencyFilter(id=agency_id))
    return new_agency[0] if new_agency else None


@router.post(path="/writer", status_code=202)
async def route_post_writer(
    writer_data: WriterCreate, db: AsyncSession = Depends(get_db)
):
    await create_writer(db, writer_data)


@router.get(path="/writer", response_model=list[WriterRead] | None, status_code=200)
async def route_get_writers(
    writer_data: WriterFilter = Depends(), db: AsyncSession = Depends(get_db)
):
    new_writer = await get_writers(db, writer_data)
    return new_writer


@router.get("/writer/{writer_id}", response_model=WriterRead | None, status_code=200)
async def route_get_writer_by_id(writer_id: UUID, db: AsyncSession = Depends(get_db)):
    new_writer = await get_writers(db, WriterFilter(id=writer_id))
    return new_writer[0] if new_writer else None
