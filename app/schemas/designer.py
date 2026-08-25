from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.schemas.agency import AgencyRead
from app.schemas.user import UserCreate, UserRead


class DesignerCreate(BaseModel):
    agency_id: UUID | None = None
    kind: Literal["designer"]
    user: UserCreate


class DesignerRead(BaseModel):
    id: UUID
    user: UserRead
    agency: AgencyRead | None

    model_config = ConfigDict(from_attributes=True)
