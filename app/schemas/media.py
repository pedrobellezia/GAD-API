from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.utils.types import NonEmptyStr


class MediaDesignerUpdate(BaseModel):
    designer_id: UUID | None = None


class MediaUpdate(BaseModel):
    alias: NonEmptyStr


class MediaRead(BaseModel):
    id: UUID
    designer_id: UUID | None = None
    agency_id: UUID | None = None
    alias: str
    filename: str
    media_type: str
    mime_type: str
    size_bytes: int
    url: str | None = None

    model_config = ConfigDict(from_attributes=True)
