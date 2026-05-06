from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import String, DateTime, Uuid, func, Enum as alchemyEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core import Base


class UserType(str, enum.Enum):
    admin = "admin"
    client = "client"
    writer = "writer"


class User(Base):
    """SQLAlchemy User model for database."""

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    pswd: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[UserType] = mapped_column(alchemyEnum(UserType), nullable=False)
    avatar: Mapped[str] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    client: Mapped[Optional["Client"]] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    writer: Mapped[Optional["Writer"]] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
