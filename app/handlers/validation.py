from fastapi import Request
from fastapi.exceptions import RequestValidationError, ResponseValidationError
from fastapi.responses import JSONResponse


async def request_validation_handler(_: Request, exc: RequestValidationError):
    formatted_errors = []

    for err in exc.errors():
        field = err["loc"][-1]

        formatted_errors.append({"field": field, "message": err["msg"]})

    return JSONResponse(
        status_code=422,
        content={
            "error": "RequestValidationError",
            "message": "Houve um erro de validação nos dados enviados",
            "details": formatted_errors,
        },
    )


async def response_validation_handler(_: Request, exc: ResponseValidationError):
    print(exc.errors(), flush=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "ReponseValidationError",
            "message": "Houve um erro de validação nos dados retornados pela API",
        },
    )
