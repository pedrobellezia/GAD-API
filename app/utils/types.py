from typing import Annotated

from pydantic import AfterValidator

from app.utils import non_empty, validate_cnpj

NonEmptyStr = Annotated[str, AfterValidator(non_empty)]

CNPJ = Annotated[str, AfterValidator(validate_cnpj)]

__all__ = ["NonEmptyStr", "CNPJ"]
