from typing import Optional

from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Fundacion(Base):
    __tablename__ = "fundaciones"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(100))
    descripcion: Mapped[Optional[str]] = mapped_column(Text)
    direccion: Mapped[str] = mapped_column(String(200))
    ciudad_id: Mapped[int] = mapped_column(ForeignKey("ciudades.id"))
    telefono: Mapped[Optional[str]] = mapped_column(String(20))
    email_contacto: Mapped[str] = mapped_column(String(120))
    activa: Mapped[bool] = mapped_column(Boolean, default=True)

    ciudad: Mapped["Ciudad"] = relationship()
    animales: Mapped[list["Animal"]] = relationship(back_populates="fundacion")
    trabajadores: Mapped[list["User"]] = relationship(back_populates="fundacion")
