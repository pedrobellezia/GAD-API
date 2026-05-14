from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import get_db
from app.schemas import AgencyCreate, AgencyRead, AgencyFilter
from app.services import create_agency, get_agencies

router = APIRouter()


@router.post(path="", status_code=202)
async def route_post_agency(
    agency_data: AgencyCreate, db: AsyncSession = Depends(get_db)
):
    await create_agency(db, agency_data)


@router.get(path="", response_model=list[AgencyRead] | None, status_code=200)
async def route_get_agencies(
    agency_data: AgencyFilter = Depends(), db: AsyncSession = Depends(get_db)
):
    new_agency = await get_agencies(db, agency_data)
    return new_agency


@router.get("/{agency_id}", response_model=AgencyRead | None, status_code=200)
async def route_get_agency_by_id(agency_id: UUID, db: AsyncSession = Depends(get_db)):
    new_agency = await get_agencies(db, AgencyFilter(id=agency_id))
    return new_agency[0] if new_agency else None
