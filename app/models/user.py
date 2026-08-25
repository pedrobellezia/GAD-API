from __future__ import annotations

import uuid
from enum import StrEnum

from sqlalchemy import DateTime, String, Uuid
from sqlalchemy import Enum as alchemyEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core import Base


class UserType(StrEnum):
    admin = "admin"
    client = "client"
    writer = "writer"
    agency = "agency"
    designer = "designer"


class User(Base):
    """SQLAlchemy User model for database."""

    __tablename__ = "users"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    pswd: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[UserType] = mapped_column(alchemyEnum(UserType), nullable=False)
    avatar: Mapped[str] = mapped_column(String(255), nullable=True)
    deleted_at: Mapped[DateTime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )

    client: Mapped[Client | None] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    writer: Mapped[Writer | None] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    agency: Mapped[Agency | None] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    designer: Mapped[Designer | None] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
