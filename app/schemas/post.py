from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models import Post, PostStatus
from app.schemas.comment import CommentBaseRead
from app.schemas.postmedia import PostMediaCreate, PostMediaRead
from app.schemas.user import UserSummary
from app.utils.types import NonEmptyStr


class PostCreate(BaseModel):
    title: NonEmptyStr
    content: NonEmptyStr
    client_id: UUID
    medias: list[PostMediaCreate] | None = None


class PostUpdate(BaseModel):
    title: NonEmptyStr | None = None
    content: NonEmptyStr | None = None
    client_id: UUID | None = None
    version: int
    medias: list[PostMediaCreate] | None = None


class PostStatusUpdate(BaseModel):
    status: PostStatus
    version: int


class PostWriterUpdate(BaseModel):
    writer_id: UUID | None = None
    version: int


class PostRead(BaseModel):
    id: UUID
    title: str
    content: str
    status: PostStatus
    version: int
    agency_id: UUID | None = None
    client_id: UUID | None = None
    writer_id: UUID | None = None
    client: UserSummary | None = None
    writer: UserSummary | None = None
    medias: list[PostMediaRead] = []
    comments: list[CommentBaseRead] = []
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_validator("client", "writer", mode="before")
    @classmethod
    def _profile_to_user(cls, value):
        # Post.client e Post.writer são perfis; expõe só o resumo público do usuário.
        # Usuário desativado fica oculto pela RLS e vira None.
        return getattr(value, "user", value) if value is not None else None


class PostFilter(BaseModel):
    id: list[UUID] | None = None
    title: str | None = None
    status: list[PostStatus] | None = None
    agency_id: list[UUID] | None = None
    client_id: list[UUID] | None = None
    writer_id: list[UUID] | None = None
    order_by: Literal["new", "old"] = "new"
    skip: int = Field(default=0, ge=0)
    limit: int = Field(default=100, ge=1, le=1000)

    def apply_filters(self, query):
        if self.id:
            query = query.where(Post.id.in_(self.id))

        if self.title:
            query = query.where(Post.title.ilike(f"%{self.title}%"))

        if self.status:
            query = query.where(Post.status.in_(self.status))

        if self.agency_id:
            query = query.where(Post.agency_id.in_(self.agency_id))

        if self.client_id:
            query = query.where(Post.client_id.in_(self.client_id))

        if self.writer_id:
            query = query.where(Post.writer_id.in_(self.writer_id))

        if self.order_by == "old":
            query = query.order_by(Post.created_at.asc())
        else:
            query = query.order_by(Post.created_at.desc())

        query = query.offset(self.skip).limit(self.limit)
        return query
