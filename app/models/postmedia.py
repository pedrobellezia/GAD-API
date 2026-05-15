from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, Uuid, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core import Base


class PostMedia(Base):
    __tablename__ = "post_medias"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)

    post_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("posts.id", ondelete="CASCADE"), nullable=False, index=True
    )

    media_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("medias.id", ondelete="CASCADE"), nullable=False, index=True
    )

    position = mapped_column(Integer, default=0, nullable=False)

    post = relationship("Post", back_populates="medias")
    media = relationship("Media", back_populates="post_medias")
