import hashlib
from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator

from app.models import User, UserType
from app.utils.types import NonEmptyStr, NormalizedEmail


class UserCreate(BaseModel):
    name: NonEmptyStr
    email: NormalizedEmail
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
    email: NormalizedEmail | None = None
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


# Caminho servido por `GET /users/{user_id}/avatar` (app/router/user.py)
USER_AVATAR_PATH = "/users/{user_id}/avatar"


def user_avatar_url(user: User) -> str | None:
    if not user.avatar:
        return None
    version = hashlib.sha256(user.avatar.encode()).hexdigest()[:12]
    return f"{USER_AVATAR_PATH.format(user_id=user.id)}?v={version}"


class UserSummary(BaseModel):
    """Dados públicos de um usuário: nunca inclui e-mail."""

    id: UUID
    name: str
    type: UserType
    avatar_url: str | None = None

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="before")
    @classmethod
    def _from_user(cls, data):
        if isinstance(data, User):
            return {
                "id": data.id,
                "name": data.name,
                "type": data.type,
                "avatar_url": user_avatar_url(data),
            }
        return data
