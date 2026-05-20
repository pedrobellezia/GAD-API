from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, Uuid, Integer, CheckConstraint, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core import Base


class PostMedia(Base):
    __tablename__ = "post_medias"

    __table_args__ = (
        CheckConstraint("position >= 0", name="ck_post_media_position_non_negative"),
        UniqueConstraint("post_id", "position", name="uq_post_media_post_id_position"),
        UniqueConstraint("post_id", "media_id", name="uq_post_media_post_id_media_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)

    post_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("posts.id", ondelete="CASCADE"), nullable=False, index=True
    )

    media_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("medias.id", ondelete="CASCADE"), nullable=False, index=True
    )

    position: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    post: Mapped["Post"] = relationship("Post", back_populates="medias")
    media: Mapped["Media"] = relationship("Media", back_populates="post_medias")
