from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel

from app.utils import NonEmpyStr


class AgencyCreate(BaseModel):
    name: NonEmpyStr
    cnpj: NonEmpyStr


class AgencyRead(BaseModel):
    id: UUID
    name: str
    cnpj: str
    created_at: datetime


class AgencyFilter(BaseModel):
    id: Optional[UUID] = None
    name: Optional[str] = None
    cnpj: Optional[str] = None
    skip: Optional[int] = 0
    limit: Optional[int] = 100
