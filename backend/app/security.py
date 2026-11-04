"""Utilidades de seguridad: hash de contraseñas y tokens de sesión (JWT)."""
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from .config import settings

ALGORITMO = "HS256"
COOKIE_SESION = "portal_sesion"


def hash_password(plain: str) -> str:
    # bcrypt incluye una "sal" aleatoria: dos usuarios con la misma
    # contraseña tienen hashes distintos.
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


# Hash de una contraseña que nadie tiene. Se usa cuando el correo no existe,
# para que el login tarde lo mismo y no revele qué correos están registrados.
HASH_SEÑUELO = hash_password("usuario-inexistente-no-usar")


def crear_token(usuario_id: int) -> str:
    """El token solo lleva el ID del usuario.

    El rol y el departamento NO van en el token: se leen de la BD en cada
    request. Así, si se desactiva un usuario o se le cambia el rol, el
    cambio aplica de inmediato y no cuando expire el token.
    """
    ahora = datetime.now(timezone.utc)
    payload = {
        "sub": str(usuario_id),
        "iat": ahora,
        "exp": ahora + timedelta(minutes=settings.jwt_expire_minutes),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=ALGORITMO)


def leer_token(token: str) -> int | None:
    """Devuelve el ID de usuario si el token es válido y no ha expirado."""
    try:
        # algorithms=[...] explícito: evita el ataque de aceptar alg="none"
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[ALGORITMO])
        return int(payload["sub"])
    except (jwt.PyJWTError, KeyError, ValueError):
        return None
