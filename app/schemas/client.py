from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class ClientCreate(BaseModel):
    id: UUID
    agencyId: UUID


class ClientRead(BaseModel):
    id: UUID
    agencyId: UUID


class ClientFilter(BaseModel):
    id: Optional[UUID] = None
    user_name: Optional[str] = None
    agency_cnpj: Optional[str] = None
    agency_name: Optional[str] = None
    skip: int = 0
    limit: int = 100
