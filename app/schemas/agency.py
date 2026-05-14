# importar diretamente pra evitar circular import
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, field_validator, EmailStr, Field
from pydantic_core import PydanticCustomError

from app.models import UserType
from app.schemas.user import UserCreate, UserRead
from app.utils import CNPJ


class AgencyCreate(BaseModel):
    cnpj: CNPJ
    user: UserCreate

    @field_validator("user")
    @classmethod
    def validate_user_type(cls, user: UserCreate):
        if user.type != UserType.agency:
            raise PydanticCustomError(
                "invalid_user_type", "tipo do usuario deve ser 'agency'"
            )
        return user


class AgencyRead(BaseModel):
    id: UUID
    cnpj: CNPJ
    user: UserRead


class AgencyFilter(BaseModel):
    id: Optional[UUID] = None
    user_email: Optional[EmailStr] = None
    user_name: Optional[str] = None
    cnpj: Optional[CNPJ] = None
    skip: int = Field(0, ge=0)
    limit: int = Field(100, ge=1, le=1000)
