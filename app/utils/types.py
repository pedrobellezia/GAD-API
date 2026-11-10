from typing import Annotated

from pydantic import AfterValidator, EmailStr

from app.utils import non_empty, normalize_email, validate_cnpj

NonEmptyStr = Annotated[str, AfterValidator(non_empty)]

NormalizedEmail = Annotated[EmailStr, AfterValidator(normalize_email)]

CNPJ = Annotated[str, AfterValidator(validate_cnpj)]

__all__ = ["NonEmptyStr", "NormalizedEmail", "CNPJ"]
