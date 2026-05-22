from typing import Optional, Literal
from uuid import UUID

from pydantic import BaseModel, field_validator, ConfigDict
from pydantic_core import PydanticCustomError

from app.models import UserType
from app.schemas import AgencyRead

from app.schemas.user import UserCreate, UserRead


class DesignerCreate(BaseModel):
    agency_id: Optional[UUID] = None
    kind: Literal["designer"]
    user: UserCreate

    @field_validator("user")
    @classmethod
    def validate_user_type(cls, user: UserCreate):
        if user.type != UserType.designer:
            raise PydanticCustomError(
                "invalid_user_type", "tipo do usuario deve ser 'designer'"
            )
        return user


class DesignerRead(BaseModel):
    id: UUID
    user: UserRead
    agency: AgencyRead | None

    model_config = ConfigDict(from_attributes=True)
