from typing import Annotated

from pydantic import BaseModel, EmailStr, Field

from app.schemas import ClientCreate, WriterCreate, AgencyCreate
from app.utils import NonEmptyStr


class LoginPayload(BaseModel):
    email: EmailStr
    pswd: NonEmptyStr


RegisterPayload = Annotated[
    ClientCreate | WriterCreate | AgencyCreate, Field(discriminator="type")
]
