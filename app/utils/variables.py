from typing import Annotated

from pydantic import AfterValidator

from app.utils.funcs import non_empty

NonEmptyStr = Annotated[str, AfterValidator(non_empty)]
