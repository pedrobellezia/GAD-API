from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.utils import NonEmptyStr


class InviteTokenBatchCreate(BaseModel):
    quantity: Annotated[int, Field(ge=1, le=100)] = 1


class InviteTokenRead(BaseModel):
    token: str
    agency_id: UUID

    model_config = ConfigDict(from_attributes=True)


class InviteTokenPayload(BaseModel):
    token: NonEmptyStr
