from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String, Text, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        Index("uq_users_username_lower", text("lower(username)"), unique=True),
        Index("uq_users_email_lower", text("lower(email)"), unique=True),
        Index("uq_users_cedula", "cedula", unique=True),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    nombres_completos: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    cedula: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    telefono: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    provincia_id: Mapped[Optional[int]] = mapped_column(ForeignKey("provincias.id"), nullable=True)
    ciudad_id: Mapped[Optional[int]] = mapped_column(ForeignKey("ciudades.id"), nullable=True)
    direccion: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    rol: Mapped[str] = mapped_column(String(20), default="adoptante")
    activo: Mapped[bool] = mapped_column(Boolean, default=True)
    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    # Solo los trabajadores pertenecen a una fundación
    fundacion_id: Mapped[Optional[int]] = mapped_column(ForeignKey("fundaciones.id"))

    fundacion: Mapped[Optional["Fundacion"]] = relationship(back_populates="trabajadores")
    provincia: Mapped[Optional["Provincia"]] = relationship(foreign_keys=[provincia_id])
    ciudad: Mapped[Optional["Ciudad"]] = relationship(foreign_keys=[ciudad_id])
