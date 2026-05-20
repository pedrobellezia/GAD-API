from typing import Annotated

from pydantic import BaseModel, EmailStr, Field

from app.schemas.client import ClientCreate
from app.schemas.agency import AgencyCreate
from app.schemas.writer import WriterCreate
from app.utils.types import NonEmptyStr


class LoginPayload(BaseModel):
    email: EmailStr
    pswd: NonEmptyStr


class LoginResponse(BaseModel):
    token: str


RegisterPayload = Annotated[
    ClientCreate | WriterCreate | AgencyCreate, Field(discriminator="kind")
]
