"""Pruebas de la configuración: la app no debe arrancar con valores inseguros."""
import pytest
from pydantic import ValidationError

from app.config import Settings

SECRETO = "clave-solo-para-pruebas-" + "x" * 32


def _config(**valores) -> Settings:
    return Settings(_env_file=None, jwt_secret=SECRETO, **valores)


def test_app_env_mal_escrito_no_arranca():
    with pytest.raises(ValidationError):
        _config(app_env="prod")


def test_produccion_sin_cookie_segura_no_arranca():
    with pytest.raises(ValidationError, match="COOKIE_SECURE"):
        _config(app_env="production", cookie_secure=False)


def test_produccion_con_cookie_segura_arranca():
    assert _config(app_env="production", cookie_secure=True).is_production


def test_desarrollo_sin_cookie_segura_arranca():
    assert not _config(app_env="development", cookie_secure=False).is_production
