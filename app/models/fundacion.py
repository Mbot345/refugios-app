from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Refugio(Base):
    __tablename__ = "refugios"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(100))
    direccion: Mapped[str] = mapped_column(String(200))
    ciudad: Mapped[str] = mapped_column(String(80))
    telefono: Mapped[str | None] = mapped_column(String(20))

    mascotas: Mapped[list["Mascota"]] = relationship(back_populates="refugio")