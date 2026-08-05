from typing import Optional, Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, ConfigDict

from app.schemas.agency import AgencyRead
from app.schemas.user import UserCreate, UserRead


class WriterCreate(BaseModel):
    kind: Literal["writer"]
    agency_id: Optional[UUID] = None
    user: UserCreate


class WriterReadNoAgency(BaseModel):
    id: UUID
    user: UserRead

    model_config = ConfigDict(from_attributes=True)


class WriterRead(BaseModel):
    id: UUID
    user: UserRead
    agency: AgencyRead | None

    model_config = ConfigDict(from_attributes=True)


class WriterFilter(BaseModel):
    id: Optional[UUID] = None
    user_name: Optional[str] = None
    user_email: Optional[EmailStr] = None
    agency_cnpj: Optional[str] = None
    agency_name: Optional[str] = None
    skip: Annotated[int, Field(ge=0)] = 0
    limit: Annotated[int, Field(ge=1, le=1000)] = 100
