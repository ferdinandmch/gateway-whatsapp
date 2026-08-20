import re

_WHATSAPP_SUFFIX = "@s.whatsapp.net"
_MIN_DIGITS = 10
_MAX_DIGITS = 13


def validate_phone_format(number: str) -> None:
    digits = re.sub(r"\D", "", number)
    if len(digits) < _MIN_DIGITS or len(digits) > _MAX_DIGITS:
        raise ValueError(
            f"Número de telefone inválido: esperado entre {_MIN_DIGITS} e {_MAX_DIGITS} dígitos, "
            f"recebido {len(digits)}."
        )


def normalize_phone(number: str) -> str:
    if number.endswith(_WHATSAPP_SUFFIX):
        return number

    digits = re.sub(r"\D", "", number)

    if not digits.startswith("55"):
        digits = "55" + digits

    return digits + _WHATSAPP_SUFFIX
