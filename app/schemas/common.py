from typing import Any

from pydantic import BaseModel

from app.utils.types import NonEmptyStr


class DetailsResponse(BaseModel):
    details: NonEmptyStr
    errors: list[dict[str, Any]] | None = None

    model_config = {"extra": "forbid"}
