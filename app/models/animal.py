import uuid
from datetime import date, datetime
from typing import Optional

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Animal(Base):
    __tablename__ = "animales"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(80))
    especie: Mapped[str] = mapped_column(String(30))
    raza: Mapped[Optional[str]] = mapped_column(String(80))
    sexo: Mapped[str] = mapped_column(String(10))
    tamano: Mapped[str] = mapped_column(String(20))
    edad_meses: Mapped[Optional[int]] = mapped_column()
    descripcion: Mapped[Optional[str]] = mapped_column(Text)
    estado: Mapped[str] = mapped_column(String(20), default="disponible")
    estado_salud: Mapped[str] = mapped_column(String(100), default="Sin evaluar")
    qr_token: Mapped[str] = mapped_column(
        String(36), unique=True, index=True, default=lambda: str(uuid.uuid4())
    )
    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    fundacion_id: Mapped[int] = mapped_column(ForeignKey("fundaciones.id"))

    fundacion: Mapped["Fundacion"] = relationship(back_populates="animales")
    fotos: Mapped[list["FotoAnimal"]] = relationship(
        back_populates="animal", cascade="all, delete-orphan"
    )
    registros_sanitarios: Mapped[list["RegistroSanitario"]] = relationship(
        back_populates="animal", cascade="all, delete-orphan"
    )
    solicitudes: Mapped[list["SolicitudPreadopcion"]] = relationship(
        back_populates="animal"
    )


class FotoAnimal(Base):
    __tablename__ = "fotos_animal"

    id: Mapped[int] = mapped_column(primary_key=True)
    ruta: Mapped[str] = mapped_column(String(255))
    es_principal: Mapped[bool] = mapped_column(Boolean, default=False)
    animal_id: Mapped[int] = mapped_column(ForeignKey("animales.id", ondelete="CASCADE"))

    animal: Mapped["Animal"] = relationship(back_populates="fotos")


class RegistroSanitario(Base):
    __tablename__ = "registros_sanitarios"

    id: Mapped[int] = mapped_column(primary_key=True)
    tipo: Mapped[str] = mapped_column(String(30))
    descripcion: Mapped[str] = mapped_column(Text)
    fecha: Mapped[date] = mapped_column(Date)
    animal_id: Mapped[int] = mapped_column(ForeignKey("animales.id", ondelete="CASCADE"))

    animal: Mapped["Animal"] = relationship(back_populates="registros_sanitarios")