import os

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str

    model_config = SettingsConfigDict(env_file=".env")

    @field_validator("DATABASE_URL")
    @classmethod
    def usar_driver_psycopg(cls, valor: str) -> str:
        """Acepta la URL como la entrega Neon y la adapta al driver psycopg."""
        for prefijo in ("postgresql://", "postgres://"):
            if valor.startswith(prefijo):
                return valor.replace(prefijo, "postgresql+psycopg://", 1)
        return valor


settings = Settings()

# Vercel define esta variable automáticamente en sus despliegues
EN_VERCEL = bool(os.getenv("VERCEL"))