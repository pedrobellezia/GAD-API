from typing import Optional
from uuid import UUID

from pydantic import BaseModel, field_validator, EmailStr, Field
from pydantic_core import PydanticCustomError

from app.models import UserType
from app.schemas import UserRead, AgencyRead

# importar diretamente pra evitar circular import
from app.schemas.user import UserCreate


class WriterCreate(BaseModel):
    agency_id: UUID
    user: UserCreate

    @field_validator("user")
    @classmethod
    def validate_user_type(cls, user: UserCreate):
        if user.type != UserType.writer:
            raise PydanticCustomError(
                "invalid_user_type", "tipo do usuario deve ser 'writer'"
            )
        return user


class WriterRead(BaseModel):
    id: UUID
    user: UserRead
    agency: AgencyRead


class WriterFilter(BaseModel):
    id: Optional[UUID] = None
    user_name: Optional[str] = None
    user_email: Optional[EmailStr] = None
    agency_cnpj: Optional[str] = None
    agency_name: Optional[str] = None
    skip: int = Field(0, ge=0)
    limit: int = Field(100, ge=1, le=1000)
