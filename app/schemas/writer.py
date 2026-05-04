from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class WriterCreate(BaseModel):
    id: UUID
    agencyId: UUID


class WriterRead(BaseModel):
    id: UUID
    agencyId: UUID


class WriterFilter(BaseModel):
    id: Optional[UUID] = None
    user_name: Optional[str] = None
    agency_cnpj: Optional[str] = None
    agency_name: Optional[str] = None
    skip: int = 0
    limit: int = 100
