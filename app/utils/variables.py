from typing import Annotated

from pydantic import AfterValidator

from app.utils import non_empty

NonEmpyStr = Annotated[str, AfterValidator(non_empty)]
