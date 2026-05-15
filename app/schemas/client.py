from typing import Optional, Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, field_validator, EmailStr, Field, ConfigDict
from pydantic_core import PydanticCustomError

from app.models import UserType
from app.schemas import AgencyRead

# importar diretamente pra evitar circular import
from app.schemas.user import UserCreate, UserRead


class ClientCreate(BaseModel):
    agency_id: Optional[UUID] = None
    kind: Literal["client"]
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
    user: UserRead
    agency: AgencyRead | None

    model_config = ConfigDict(from_attributes=True)


class ClientFilter(BaseModel):
    id: Optional[UUID] = None
    user_name: Optional[str] = None
    user_email: Optional[EmailStr] = None
    agency_cnpj: Optional[str] = None
    agency_name: Optional[str] = None
    skip: Annotated[int, Field(ge=0)] = 0
    limit: Annotated[int, Field(ge=1, le=1000)] = 100
