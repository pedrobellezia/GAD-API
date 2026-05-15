from __future__ import annotations

import enum
import uuid
from typing import Optional, Any

from sqlalchemy import String, Uuid, Enum as alchemyEnum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core import Base


class UserType(str, enum.Enum):
    admin = "admin"
    client = "client"
    writer = "writer"
    agency = "agency"


class User(Base):
    """SQLAlchemy User model for database."""

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    pswd: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[UserType] = mapped_column(alchemyEnum(UserType), nullable=False)
    avatar: Mapped[str] = mapped_column(String(255), nullable=True)
    token: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid, ForeignKey("invite_tokens.token"), unique=True, nullable=True
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
    token_info: Mapped[Any] = relationship(
        back_populates="used_by", uselist=False, cascade="all, delete-orphan"
    )
