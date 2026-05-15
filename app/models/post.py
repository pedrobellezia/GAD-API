from __future__ import annotations

import uuid
from enum import Enum

from sqlalchemy import (
    Enum as SQLEnum,
    ForeignKey,
    String,
    Text,
    Uuid,
    Integer,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core import Base


class PostStatus(str, Enum):
    draft = "draft"
    review = "review"
    approved = "approved"
    denied = "denied"
    published = "published"


class Post(Base):
    __tablename__ = "posts"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)

    agency_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("agencies.id", ondelete="CASCADE"), nullable=False
    )

    client_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("clients.id", ondelete="CASCADE"), nullable=False
    )

    created_by_writer_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("writers.id", ondelete="SET NULL"), nullable=True
    )

    updated_by_writer_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("writers.id", ondelete="SET NULL"), nullable=True
    )

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)

    status: Mapped[PostStatus] = mapped_column(
        SQLEnum(PostStatus, name="poststatus"),
        default=PostStatus.draft,
        nullable=False,
    )

    version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
    )

    agency = relationship("Agency")
    client = relationship("Client")

    created_by_writer = relationship("Writer", foreign_keys=[created_by_writer_id])
    updated_by_writer = relationship("Writer", foreign_keys=[updated_by_writer_id])

    medias = relationship(
        "PostMedia", back_populates="post", cascade="all, delete-orphan"
    )
