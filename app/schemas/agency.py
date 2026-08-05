from typing import Optional, Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, ConfigDict

from app.schemas.user import UserCreate, UserRead
from app.utils.types import CNPJ


class AgencyCreate(BaseModel):
    cnpj: CNPJ
    user: UserCreate
    kind: Literal["agency"]


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
