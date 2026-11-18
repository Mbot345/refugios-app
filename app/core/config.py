import os

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    
        # Correo (SMTP). Si SMTP_USER está vacío, los correos se simulan en la consola.
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = ""
    # Dirección pública de la app, para los enlaces de los correos
    APP_URL: str = "http://localhost:8000"

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