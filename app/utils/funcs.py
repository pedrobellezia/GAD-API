from pydantic_core import PydanticCustomError
import re


def non_empty(value):
    if not value or not value.strip():
        raise PydanticCustomError("non_empty", "Value must be a non-empty string")
    return value


def validate_cnpj(cnpj: str) -> str:
    cnpj = re.sub(r"\D", "", cnpj)

    if len(cnpj) != 14:
        raise ValueError("CNPJ inválido")

    # evita sequências
    if cnpj == cnpj[0] * 14:
        raise ValueError("CNPJ inválido")

    def calc_digit(cnpj_partial: str, weights: list[int]) -> str:
        total = sum(int(num) * weight for num, weight in zip(cnpj_partial, weights))

        remainder = total % 11
        digit = 0 if remainder < 2 else 11 - remainder

        return str(digit)

    first_weights = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    second_weights = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]

    first_digit = calc_digit(cnpj[:12], first_weights)
    second_digit = calc_digit(cnpj[:12] + first_digit, second_weights)

    if cnpj[-2:] != first_digit + second_digit:
        raise PydanticCustomError("invalid_cnpj", "CNPJ inválido")

    return cnpj
