from typing import Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict


class MediaRead(BaseModel):
    id: UUID
    designer_id: Optional[UUID] = None
    agency_id: Optional[UUID] = None
    alias: str
    filename: str
    media_type: str
    mime_type: str
    size_bytes: int

    model_config = ConfigDict(from_attributes=True)
