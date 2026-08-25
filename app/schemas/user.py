from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models import User, UserType
from app.utils.types import NonEmptyStr


class UserCreate(BaseModel):
    name: NonEmptyStr
    email: EmailStr
    avatar: NonEmptyStr | None = None
    pswd: NonEmptyStr


class UserRead(BaseModel):
    id: UUID
    name: str
    email: EmailStr
    type: UserType
    avatar: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserFilter(BaseModel):
    id: UUID | None = None
    name: str | None = None
    email: EmailStr | None = None
    type: UserType | None = None
    order_by: Literal["new", "old"] = "new"
    skip: Annotated[int, Field(ge=0)] = 0
    limit: Annotated[int, Field(ge=1, le=1000)] = 100

    def apply_filters(self, query):
        if self.id:
            query = query.where(User.id == self.id)

        if self.name:
            query = query.where(User.name.ilike(f"%{self.name}%"))

        if self.email:
            query = query.where(User.email == self.email)

        if self.type:
            query = query.where(User.type == self.type)

        if self.order_by == "old":
            query = query.order_by(User.created_at.asc())
        else:
            query = query.order_by(User.created_at.desc())

        query = query.offset(self.skip).limit(self.limit)
        return query
