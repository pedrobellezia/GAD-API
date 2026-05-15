from __future__ import annotations

import uuid
from datetime import datetime
from typing import List

from sqlalchemy import String, DateTime, Uuid, func, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core import Base


class Agency(Base):
    __tablename__ = "agencies"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id"), primary_key=True
    )
    cnpj: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    user: Mapped["User"] = relationship(back_populates="agency")

    clients: Mapped[List["Client"]] = relationship(
        back_populates="agency", cascade="all, delete-orphan"
    )
    writers: Mapped[List["Writer"]] = relationship(
        back_populates="agency", cascade="all, delete-orphan"
    )
    invite_tokens: Mapped[List["InviteToken"]] = relationship(
        back_populates="agency", cascade="all, delete-orphan"
    )
