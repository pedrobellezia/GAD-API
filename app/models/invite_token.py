from __future__ import annotations

import uuid
from datetime import datetime, timedelta

from sqlalchemy import ForeignKey, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core import Base
from app.core.config import INVITE_TOKEN_TTL_DAYS


class InviteToken(Base):
    __tablename__ = "invite_tokens"

    token: Mapped[str] = mapped_column(String(64), primary_key=True)

    agency_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("agencies.id", ondelete="CASCADE"), nullable=False
    )

    agency: Mapped[Agency] = relationship(back_populates="invite_tokens")

    @property
    def expires_at(self) -> datetime:
        return self.created_at + timedelta(days=INVITE_TOKEN_TTL_DAYS)
