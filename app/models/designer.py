from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core import Base


class Designer(Base):
    __tablename__ = "designers"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    agency_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("agencies.id", ondelete="SET NULL"), nullable=True
    )

    user: Mapped[User] = relationship(back_populates="designer")
    agency: Mapped[Agency] = relationship(back_populates="designers")
    medias: Mapped[list[Media]] = relationship("Media", back_populates="designer")
