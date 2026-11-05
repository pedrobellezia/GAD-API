from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class AuditLogRead(BaseModel):
    id: UUID
    agency_id: UUID | None
    actor_id: UUID | None
    actor_name: str
    actor_email: str
    action: str
    resource_type: str
    resource_id: UUID | None
    resource_name: str | None
    message: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
