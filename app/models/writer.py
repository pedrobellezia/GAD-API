from __future__ import annotations

import uuid
from sqlalchemy import Uuid, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core import Base


class Writer(Base):
    __tablename__ = "writers"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id"), primary_key=True
    )
    agency_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("agencies.id"), nullable=True
    )

    user: Mapped["User"] = relationship(back_populates="writer")
    agency: Mapped["Agency"] = relationship(back_populates="writers")
    posts: Mapped[list["Post"]] = relationship(
        back_populates="writer", cascade="all, delete-orphan"
    )
