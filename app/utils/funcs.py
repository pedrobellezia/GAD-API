from pydantic_core import PydanticCustomError


def non_empty(value):
    if not value or not value.strip():
        raise PydanticCustomError("non_empty", "Value must be a non-empty string")
    return value
