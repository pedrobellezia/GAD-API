from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.schemas.media import MediaRead


class PostMediaCreate(BaseModel):
    media_id: UUID
    position: int = 0


class PostMediaRead(BaseModel):
    position: int
    media: MediaRead

    model_config = ConfigDict(from_attributes=True)
