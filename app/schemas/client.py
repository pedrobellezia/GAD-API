from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models import Agency, Client, User
from app.schemas.agency import AgencyRead
from app.schemas.user import UserCreate, UserRead


class ClientCreate(BaseModel):
    agency_id: UUID | None = None
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
    id: UUID | None = None
    user_name: str | None = None
    user_email: EmailStr | None = None
    agency_cnpj: str | None = None
    agency_name: str | None = None
    order_by: Literal["new", "old"] = "new"
    page: Annotated[int, Field(ge=1)] = 1
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

        query = query.offset((self.page - 1) * self.limit).limit(self.limit)
        return query
