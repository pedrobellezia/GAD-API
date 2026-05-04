import uuid
from sqlalchemy import Uuid, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core import Base


class Client(Base):
    __tablename__ = "clients"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id"), primary_key=True)
    agencyId: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("agencies.id"), nullable=False)

    user: Mapped["User"] = relationship(back_populates="client")
    agency: Mapped["Agency"] = relationship(back_populates="clients")
