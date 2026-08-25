from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models import Agency, User
from app.schemas.user import UserCreate, UserRead
from app.utils.types import CNPJ


class AgencyCreate(BaseModel):
    cnpj: CNPJ
    user: UserCreate
    kind: Literal["agency"]


class AgencyRead(BaseModel):
    id: UUID
    cnpj: CNPJ
    user: UserRead

    model_config = ConfigDict(from_attributes=True)


class AgencyFilter(BaseModel):
    id: UUID | None = None
    user_email: EmailStr | None = None
    user_name: str | None = None
    cnpj: str | None = None
    order_by: Literal["new", "old"] = "new"
    skip: Annotated[int, Field(ge=0)] = 0
    limit: Annotated[int, Field(ge=1)] = 100

    def apply_filters(self, query):
        if self.id:
            query = query.where(Agency.id == self.id)

        if self.cnpj:
            query = query.where(Agency.cnpj == self.cnpj)

        if self.user_email:
            query = query.where(User.email == self.user_email)

        if self.user_name:
            query = query.where(User.name.ilike(f"%{self.user_name}%"))

        if self.order_by == "old":
            query = query.order_by(Agency.created_at.asc())
        else:
            query = query.order_by(Agency.created_at.desc())

        query = query.offset(self.skip).limit(self.limit)
        return query
