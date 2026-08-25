from __future__ import annotations

import uuid
from enum import StrEnum

from sqlalchemy import (
    Enum as SQLEnum,
)
from sqlalchemy import (
    ForeignKey,
    Integer,
    String,
    Text,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core import Base


class PostStatus(StrEnum):
    draft = "draft"
    review = "review"
    approved = "approved"
    denied = "denied"
    published = "published"


class Post(Base):
    __tablename__ = "posts"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)

    agency_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("agencies.id", ondelete="SET NULL"), nullable=True
    )

    client_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("clients.id", ondelete="SET NULL"), nullable=True
    )

    writer_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("writers.id", ondelete="SET NULL"), nullable=True
    )

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)

    version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
    )

    __mapper_args__ = {"version_id_col": version}

    status: Mapped[PostStatus] = mapped_column(
        SQLEnum(PostStatus, name="poststatus"),
        default=PostStatus.draft,
        nullable=False,
    )

    agency: Mapped[Agency] = relationship(back_populates="posts")
    client: Mapped[Client] = relationship(back_populates="posts")
    writer: Mapped[Writer] = relationship(back_populates="posts")

    medias: Mapped[list[PostMedia]] = relationship(
        "PostMedia",
        back_populates="post",
        cascade="all, delete-orphan",
    )
