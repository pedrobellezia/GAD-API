from datetime import datetime
from typing import Optional, List, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models import Post, PostStatus
from app.utils.types import NonEmptyStr
from app.schemas.postmedia import PostMediaCreate, PostMediaRead


class PostCreate(BaseModel):
    title: NonEmptyStr
    content: NonEmptyStr
    client_id: UUID
    medias: Optional[List[PostMediaCreate]] = None


class PostUpdate(BaseModel):
    title: Optional[NonEmptyStr] = None
    content: Optional[NonEmptyStr] = None
    client_id: Optional[UUID] = None
    status: Optional[PostStatus] = None
    version: int
    medias: Optional[List[PostMediaCreate]] = None


class PostRead(BaseModel):
    id: UUID
    title: str
    content: str
    status: PostStatus
    version: int
    agency_id: Optional[UUID] = None
    client_id: Optional[UUID] = None
    writer_id: Optional[UUID] = None
    medias: List[PostMediaRead] = []
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PostFilter(BaseModel):
    id: Optional[UUID] = None
    title: Optional[str] = None
    status: Optional[PostStatus] = None
    agency_id: Optional[UUID] = None
    client_id: Optional[UUID] = None
    writer_id: Optional[UUID] = None
    order_by: Literal["new", "old"] = "new"
    skip: int = Field(default=0, ge=0)
    limit: int = Field(default=100, ge=1, le=1000)

    def apply_filters(self, query):
        if self.id:
            query = query.where(Post.id == self.id)

        if self.title:
            query = query.where(Post.title.ilike(f"%{self.title}%"))

        if self.status:
            query = query.where(Post.status == self.status)

        if self.agency_id:
            query = query.where(Post.agency_id == self.agency_id)

        if self.client_id:
            query = query.where(Post.client_id == self.client_id)

        if self.writer_id:
            query = query.where(Post.writer_id == self.writer_id)

        if self.order_by == "old":
            query = query.order_by(Post.created_at.asc())
        else:
            query = query.order_by(Post.created_at.desc())

        query = query.offset(self.skip).limit(self.limit)
        return query
