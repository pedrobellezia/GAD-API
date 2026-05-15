from typing import Annotated

from pydantic import BaseModel, EmailStr, Field

from app.schemas.client import ClientCreate
from app.schemas.agency import AgencyCreate
from app.schemas.writer import WriterCreate
from app.utils import NonEmptyStr


class LoginPayload(BaseModel):
    email: EmailStr
    pswd: NonEmptyStr


RegisterPayload = Annotated[
    ClientCreate | WriterCreate | AgencyCreate, Field(discriminator="kind")
]
