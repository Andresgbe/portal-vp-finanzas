"""Utilidades de seguridad: hash de contraseñas."""
import bcrypt


def hash_password(plain: str) -> str:
    # bcrypt incluye una "sal" aleatoria: dos usuarios con la misma
    # contraseña tienen hashes distintos.
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
