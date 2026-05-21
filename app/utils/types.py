from pydantic import AfterValidator
from app.utils import non_empty, validate_cnpj
from typing import Annotated
from app.models import Client, Writer, Designer

Member = Client | Writer | Designer

NonEmptyStr = Annotated[str, AfterValidator(non_empty)]

CNPJ = Annotated[str, AfterValidator(validate_cnpj)]

__all__ = ["Member", "NonEmptyStr", "CNPJ"]
