from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from app.schemas.client import ClientCreate
from app.schemas.agency import AgencyCreate
from app.schemas.designer import DesignerCreate
from app.schemas.writer import WriterCreate
from app.utils.types import NonEmptyStr


class LoginPayload(BaseModel):
    email: EmailStr
    pswd: NonEmptyStr
    restore: bool = False


class LoginResponse(BaseModel):
    token: str


class JwtPayload(BaseModel):
    sub: UUID
    exp: int

    model_config = {"extra": "forbid"}


RegisterPayload = Annotated[
    ClientCreate | WriterCreate | AgencyCreate | DesignerCreate,
    Field(discriminator="kind"),
]
