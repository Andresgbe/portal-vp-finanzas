"""Configuración leída de variables de entorno (.env).

Ningún secreto vive en el código: si falta JWT_SECRET la aplicación
no arranca, en lugar de usar un valor por defecto inseguro.
"""
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ROOT_DIR / ".env", extra="ignore")

    app_env: str = "development"
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

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() == "production"


settings = Settings()
