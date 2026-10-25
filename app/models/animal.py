from datetime import date

from sqlalchemy import Date, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Mascota(Base):
    __tablename__ = "mascotas"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(80))
    especie: Mapped[str] = mapped_column(String(30))
    raza: Mapped[str | None] = mapped_column(String(80))
    sexo: Mapped[str] = mapped_column(String(10))
    fecha_nacimiento: Mapped[date | None] = mapped_column(Date)
    descripcion: Mapped[str | None] = mapped_column(Text)
    estado: Mapped[str] = mapped_column(String(20), default="disponible")
    refugio_id: Mapped[int] = mapped_column(ForeignKey("refugios.id"))

    refugio: Mapped["Refugio"] = relationship(back_populates="mascotas")