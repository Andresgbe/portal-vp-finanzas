"""Configuración leída de variables de entorno (.env).

Ningún secreto vive en el código: si falta JWT_SECRET la aplicación
no arranca, en lugar de usar un valor por defecto inseguro.
"""
from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ROOT_DIR / ".env", extra="ignore")

    # Solo valores conocidos: un error de tipeo como "prod" no debe hacer que
    # producción corra sin sus protecciones (sin /docs, semilla bloqueada).
    app_env: Literal["development", "test", "production"] = "development"
    database_url: str = "sqlite:///./portal.db"
    jwt_secret: str = Field(min_length=32)
    jwt_expire_minutes: int = 60
    seed_demo_password: str | None = None
    cookie_secure: bool = False

    @field_validator("jwt_secret")
    @classmethod
    def _no_placeholder(cls, v: str) -> str:
        if v.lower() in {"changeme", "secret", "secreto"}:
            raise ValueError("JWT_SECRET no puede ser un valor de ejemplo")
        return v

    @model_validator(mode="after")
    def _cookie_segura_en_produccion(self) -> "Settings":
        # Sin esto, la cookie de sesión podría viajar por HTTP sin cifrar
        if self.is_production and not self.cookie_secure:
            raise ValueError("En producción COOKIE_SECURE debe ser true")
        return self

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


settings = Settings()
