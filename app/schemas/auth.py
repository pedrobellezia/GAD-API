from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.agency import AgencyCreate
from app.schemas.client import ClientCreate
from app.schemas.designer import DesignerCreate
from app.schemas.writer import WriterCreate
from app.utils.types import NonEmptyStr, NormalizedEmail


class LoginPayload(BaseModel):
    email: NormalizedEmail
    pswd: NonEmptyStr
    restore: bool = False


class LoginResponse(BaseModel):
    token: str


class ChangePasswordPayload(BaseModel):
    current_password: NonEmptyStr
    new_password: NonEmptyStr


class ProfileUpdatePayload(BaseModel):
    name: NonEmptyStr | None = None
    email: NormalizedEmail | None = None


class JwtPayload(BaseModel):
    sub: UUID
    exp: int

    model_config = {"extra": "forbid"}


RegisterPayload = Annotated[
    ClientCreate | WriterCreate | AgencyCreate | DesignerCreate,
    Field(discriminator="kind"),
]
