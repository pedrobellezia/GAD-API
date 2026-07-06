from __future__ import annotations

import enum
import uuid
from typing import Optional

from sqlalchemy import String, Uuid, Enum as alchemyEnum, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core import Base


class UserType(str, enum.Enum):
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
        DateTime(timezone=True),
        nullable=True,
        index=True
    )

    client: Mapped[Optional["Client"]] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    writer: Mapped[Optional["Writer"]] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    agency: Mapped[Optional["Agency"]] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    designer: Mapped[Optional["Designer"]] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
