from typing import Optional, Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, ConfigDict

from app.models import Client, Agency, User
from app.schemas.agency import AgencyRead
from app.schemas.user import UserCreate, UserRead


class ClientCreate(BaseModel):
    agency_id: Optional[UUID] = None
    kind: Literal["client"]
    user: UserCreate


class ClientRead(BaseModel):
    id: UUID
    user: UserRead
    agency: AgencyRead | None

    model_config = ConfigDict(from_attributes=True)


class ClientReadNoAgency(BaseModel):
    id: UUID
    user: UserRead

    model_config = ConfigDict(from_attributes=True)


class ClientFilter(BaseModel):
    id: Optional[UUID] = None
    user_name: Optional[str] = None
    user_email: Optional[EmailStr] = None
    agency_cnpj: Optional[str] = None
    agency_name: Optional[str] = None
    order_by: Literal["new", "old"] = "new"
    skip: Annotated[int, Field(ge=0)] = 0
    limit: Annotated[int, Field(ge=1, le=1000)] = 100

    def apply_filters(self, query, agency_user=None):
        if self.id:
            query = query.where(Client.id == self.id)

        if self.user_name:
            query = query.where(User.name.ilike(f"%{self.user_name}%"))

        if self.user_email:
            query = query.where(User.email == self.user_email)

        if self.agency_cnpj:
            query = query.where(Agency.cnpj == self.agency_cnpj)

        if self.agency_name and agency_user is not None:
            query = query.where(agency_user.name.ilike(f"%{self.agency_name}%"))

        if self.order_by == "old":
            query = query.order_by(Client.created_at.asc())
        else:
            query = query.order_by(Client.created_at.desc())

        query = query.offset(self.skip).limit(self.limit)
        return query
