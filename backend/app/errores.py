"""Convierte los errores de validación en un mensaje legible para el usuario.

Por defecto, FastAPI responde con una lista de objetos en inglés que además
repite lo que se envió en el campo "input" (incluso una contraseña). El frontend
espera en "detail" un texto en español, así que aquí se arma ese texto y nunca
se devuelve el valor recibido.
"""
from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

# Tipos de error de Pydantic -> cómo explicarlos. Los {} se llenan con los
# límites del propio error (min_length, max_length, ge...).
MENSAJES = {
    "missing": "es obligatorio",
    "string_too_short": "debe tener al menos {min_length} caracteres",
    "string_too_long": "debe tener como máximo {max_length} caracteres",
    "string_pattern_mismatch": "tiene un valor no permitido",
    "literal_error": "tiene un valor no permitido",
    "greater_than_equal": "debe ser mayor o igual a {ge}",
    "decimal_parsing": "debe ser un monto válido",
    "decimal_type": "debe ser un monto válido",
    "decimal_max_digits": "tiene demasiados dígitos",
    "decimal_whole_digits": "tiene demasiados dígitos",
    "decimal_max_places": "debe tener como máximo {decimal_places} decimales",
    "date_parsing": "debe ser una fecha válida",
    "date_from_datetime_parsing": "debe ser una fecha válida",
    "date_type": "debe ser una fecha válida",
    "int_parsing": "debe ser un número entero",
    "int_type": "debe ser un número entero",
    "bool_parsing": "debe ser verdadero o falso",
}
MENSAJE_GENERICO = "tiene un valor inválido"

NOMBRES_CAMPO = {"password": "Contraseña", "tienda_id": "Tienda", "cajero_id": "Cajero"}


def _nombre_campo(ubicacion: tuple) -> str | None:
    # La ubicación es, por ejemplo, ("body", "monto_declarado"). Sin un campo
    # concreto (JSON mal formado o cuerpo ausente) no hay nombre que mostrar.
    if len(ubicacion) < 2 or not isinstance(ubicacion[-1], str):
        return None
    campo = ubicacion[-1]
    return NOMBRES_CAMPO.get(campo, campo.replace("_", " ").capitalize())


def _explicar(error: dict) -> str:
    campo = _nombre_campo(tuple(error["loc"]))
    if campo is None:
        return "La solicitud no tiene un formato válido."
    plantilla = MENSAJES.get(error["type"], MENSAJE_GENERICO)
    return f'El campo "{campo}" {plantilla.format(**error.get("ctx", {}))}.'


async def manejar_error_validacion(_: Request, exc: RequestValidationError) -> JSONResponse:
    # dict.fromkeys quita los repetidos conservando el orden
    mensajes = dict.fromkeys(_explicar(e) for e in exc.errors())
    return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                        content={"detail": " ".join(mensajes)})
