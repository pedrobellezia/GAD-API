from __future__ import annotations

import uuid
from typing import List

from sqlalchemy import String, Uuid, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core import Base


class Agency(Base):
    __tablename__ = "agencies"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    cnpj: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)

    user: Mapped["User"] = relationship(back_populates="agency")

    clients: Mapped[List["Client"]] = relationship(back_populates="agency")
    writers: Mapped[List["Writer"]] = relationship(back_populates="agency")
    designers: Mapped[List["Designer"]] = relationship(back_populates="agency")
    invite_tokens: Mapped[List["InviteToken"]] = relationship(
        back_populates="agency", cascade="all, delete-orphan"
    )
    posts: Mapped[List["Post"]] = relationship(back_populates="agency")
    medias: Mapped[List["Media"]] = relationship(back_populates="agency")
