from typing import Optional, Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, field_validator, EmailStr, Field, ConfigDict
from pydantic_core import PydanticCustomError

from app.models import UserType
from app.schemas.user import UserCreate, UserRead
from app.utils import CNPJ


class AgencyCreate(BaseModel):
    cnpj: CNPJ
    user: UserCreate
    kind: Literal["agency"]

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

    model_config = ConfigDict(from_attributes=True)


class AgencyFilter(BaseModel):
    id: Optional[UUID] = None
    user_email: Optional[EmailStr] = None
    user_name: Optional[str] = None
    cnpj: Optional[str] = None
    skip: Annotated[int, Field(ge=0)] = 0
    limit: Annotated[int, Field(ge=1)] = 100
