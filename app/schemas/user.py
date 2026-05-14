from datetime import datetime
from typing import Optional, Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field
from app.utils import NonEmptyStr
from app.models import UserType


class UserCreate(BaseModel):
    name: NonEmptyStr
    email: EmailStr
    type: UserType
    avatar: Optional[NonEmptyStr] = None
    pswd: NonEmptyStr


class UserRead(BaseModel):
    id: UUID
    name: str
    email: EmailStr
    type: UserType
    avatar: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserFilter(BaseModel):
    id: Optional[UUID] = None
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    type: Optional[UserType] = None
    skip: Annotated[int, Field(ge=0)] = 0
    limit: Annotated[int, Field(ge=1, le=1000)] = 100
