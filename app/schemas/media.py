from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models import Media, MediaType


class MediaRead(BaseModel):
    id: UUID
    designer_id: UUID | None = None
    agency_id: UUID | None = None
    alias: str
    filename: str
    media_type: str
    mime_type: str
    size_bytes: int

    model_config = ConfigDict(from_attributes=True)


class MediaFilter(BaseModel):
    id: list[UUID] | None = None
    alias: str | None = None
    media_type: list[MediaType] | None = None
    agency_id: list[UUID] | None = None
    designer_id: list[UUID] | None = None
    order_by: Literal["new", "old"] = "new"
    page: int = Field(default=1, ge=1)
    limit: int = Field(default=100, ge=1, le=1000)

    def apply_filters(self, query):
        if self.id:
            query = query.where(Media.id.in_(self.id))

        if self.alias:
            query = query.where(Media.alias.ilike(f"%{self.alias}%"))

        if self.media_type:
            query = query.where(Media.media_type.in_(self.media_type))

        if self.agency_id:
            query = query.where(Media.agency_id.in_(self.agency_id))

        if self.designer_id:
            query = query.where(Media.designer_id.in_(self.designer_id))

        if self.order_by == "old":
            query = query.order_by(Media.created_at.asc())
        else:
            query = query.order_by(Media.created_at.desc())

        query = query.offset((self.page - 1) * self.limit).limit(self.limit)
        return query
