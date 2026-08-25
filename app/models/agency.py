from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core import Base


class Agency(Base):
    __tablename__ = "agencies"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    cnpj: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)

    user: Mapped[User] = relationship(back_populates="agency")

    clients: Mapped[list[Client]] = relationship(back_populates="agency")
    writers: Mapped[list[Writer]] = relationship(back_populates="agency")
    designers: Mapped[list[Designer]] = relationship(back_populates="agency")
    invite_tokens: Mapped[list[InviteToken]] = relationship(
        back_populates="agency", cascade="all, delete-orphan"
    )
    posts: Mapped[list[Post]] = relationship(back_populates="agency")
    medias: Mapped[list[Media]] = relationship(back_populates="agency")
