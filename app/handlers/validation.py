from fastapi import Request
from fastapi.exceptions import RequestValidationError, ResponseValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError


async def request_validation_handler(_: Request, exc: RequestValidationError):
    formatted_errors = []
    for err in exc.errors():
        print(err, flush=True)
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


async def integrity_error_handler(_: Request, exc: IntegrityError):
    # depois troca pra logger
    print(exc, flush=True)
    print("-" * 20)
    print(exc.orig, flush=True)
    code = exc.orig.sqlstate

    match code:
        case "23505":
            message = "Registro duplicado"

        case "23503":
            message = "Violação de chave estrangeira"

        case "23502":
            message = "Campo obrigatório não informado"

        case "23514":
            message = "Valor inválido para a regra da tabela"

        case _:
            message = "Erro de integridade no banco"

    return JSONResponse(
        status_code=400, content={"error": "IntegrityError", "detail": message}
    )
