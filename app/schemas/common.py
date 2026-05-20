from pydantic import BaseModel

from app.utils.types import NonEmptyStr


class DetailsResponse(BaseModel):
    details: NonEmptyStr

    model_config = {"extra": "forbid"}
