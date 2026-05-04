from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models import UserType


class UserCreate(BaseModel):
    name: str
    email: str
    type: UserType
    avatar: Optional[str] = None
    pswd: str


class UserRead(BaseModel):
    id: UUID
    name: str
    email: str
    type: UserType
    avatar: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserFilter(BaseModel):
    id: Optional[UUID] = None
    name: Optional[str] = None
    email: Optional[str] = None
    type: Optional[UserType] = None
    skip: Optional[int] = 0
    limit: Optional[int] = 100
