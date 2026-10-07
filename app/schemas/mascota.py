from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class MascotaData(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    nombre: str = Field(min_length=1, max_length=80)
    especie: str = Field(min_length=1, max_length=30)
    raza: str | None = Field(default=None, max_length=80)
    sexo: str = Field(min_length=1, max_length=10)
    fecha_nacimiento: date | None = None
    descripcion: str | None = None
    estado: Literal["disponible", "en_proceso", "adoptada"] = "disponible"
    refugio_id: int = Field(gt=0)

    @field_validator("fecha_nacimiento")
    @classmethod
    def no_fecha_futura(cls, value: date | None) -> date | None:
        if value is not None and value > date.today():
            raise ValueError("La fecha de nacimiento no puede ser futura.")
        return value

    @field_validator("raza", "descripcion", mode="before")
    @classmethod
    def texto_vacio_es_nulo(cls, value: str | None) -> str | None:
        return value or None
