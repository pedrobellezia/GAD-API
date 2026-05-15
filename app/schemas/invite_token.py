from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models import InviteTokenKind
from app.utils import NonEmptyStr


class InviteTokenBatchCreate(BaseModel):
    kind: InviteTokenKind
    quantity: Annotated[int, Field(ge=1, le=100)] = 1


class InviteTokenRead(BaseModel):
    token: str
    kind: InviteTokenKind
    agency_id: UUID
    used_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class InviteTokenPayload(BaseModel):
    token: NonEmptyStr
