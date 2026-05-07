from typing import Optional
from uuid import UUID

from pydantic import BaseModel, field_validator
from pydantic_core import PydanticCustomError

from app.models import UserType

# importar diretamente pra evitar circular import
from app.schemas.user import UserCreate


class ClientCreate(BaseModel):
    agencyId: UUID
    user: UserCreate

    @field_validator("user")
    @classmethod
    def validate_user_type(cls, user: UserCreate):
        if user.type != UserType.client:
            raise PydanticCustomError(
                "invalid_user_type", "tipo do usuario deve ser 'client'"
            )
        return user


class ClientRead(BaseModel):
    id: UUID
    agencyId: UUID


class ClientFilter(BaseModel):
    id: Optional[UUID] = None
    user_name: Optional[str] = None
    agency_cnpj: Optional[str] = None
    agency_name: Optional[str] = None
    skip: int = 0
    limit: int = 100
