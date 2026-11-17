import re

TELEFONO_MOVIL = re.compile(r"^09[0-9]{8}$")
TELEFONO_CONVENCIONAL = re.compile(r"^0[2-7][0-9]{7}$")


def cedula_valida(cedula: str) -> bool:
    """Valida una cédula ecuatoriana de 10 dígitos con el algoritmo oficial (módulo 10)."""
    if not re.fullmatch(r"[0-9]{10}", cedula):
        return False

    provincia = int(cedula[:2])
    if not (1 <= provincia <= 24 or provincia == 30):
        return False
    if int(cedula[2]) > 5:  # el tercer dígito identifica a personas naturales
        return False

    suma = 0
    for posicion, digito in enumerate(cedula[:9]):
        valor = int(digito) * (2 if posicion % 2 == 0 else 1)
        if valor > 9:
            valor -= 9
        suma += valor

    return (10 - suma % 10) % 10 == int(cedula[9])