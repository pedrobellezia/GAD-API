from __future__ import annotations

import enum
import uuid
from typing import Any

from sqlalchemy import String, Uuid, Enum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core import Base


class InviteTokenKind(str, enum.Enum):
    client = "client"
    writer = "writer"


class InviteToken(Base):
    __tablename__ = "invite_tokens"

    token: Mapped[str] = mapped_column(String(64), primary_key=True)
    kind: Mapped[InviteTokenKind] = mapped_column(Enum(InviteTokenKind), nullable=False)

    agency_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("agencies.id"), nullable=False
    )

    agency: Mapped[Any] = relationship(back_populates="invite_tokens")
    used_by: Mapped[Any] = relationship(back_populates="token_info", uselist=False)
