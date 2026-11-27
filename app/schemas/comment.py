from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.schemas.user import UserSummary
from app.utils.types import NonEmptyStr


class CommentCreate(BaseModel):
    content: NonEmptyStr


class CommentBaseRead(BaseModel):
    id: UUID
    post_id: UUID
    author_id: UUID
    content: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CommentRead(CommentBaseRead):
    author: UserSummary | None = None
