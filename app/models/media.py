from __future__ import annotations

import uuid
from enum import Enum

from sqlalchemy import Enum as SQLEnum, String, Uuid, ForeignKey, BigInteger, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core import Base


class MediaType(str, Enum):
    video = "video"
    image = "image"


class Media(Base):
    __tablename__ = "medias"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)

    designer_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("designers.id", ondelete="SET NULL"), nullable=True
    )

    alias: Mapped[str] = mapped_column(String(255), nullable=False)

    url: Mapped[str] = mapped_column(Text, nullable=False, unique=True)

    filename: Mapped[str] = mapped_column(String(255), nullable=False)

    media_type: Mapped[MediaType] = mapped_column(
        SQLEnum(MediaType, name="mediatype"),
        nullable=False,
    )

    mime_type: Mapped[str] = mapped_column(String(255), nullable=False)

    size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)

    post_medias: Mapped[list["PostMedia"]] = relationship(
        "PostMedia",
        back_populates="media",
        cascade="all, delete-orphan",
    )

    designer: Mapped["Designer"] = relationship("Designer", back_populates="medias")
