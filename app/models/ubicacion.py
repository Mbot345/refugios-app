from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Provincia(Base):
    __tablename__ = "provincias"
    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(60), unique=True)
    ciudades: Mapped[list["Ciudad"]] = relationship(
        back_populates="provincia", order_by="Ciudad.nombre"
    )


class Ciudad(Base):
    __tablename__ = "ciudades"
    __table_args__ = (
        UniqueConstraint("provincia_id", "nombre", name="uq_ciudad_provincia_nombre"),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(80))
    provincia_id: Mapped[int] = mapped_column(ForeignKey("provincias.id"))
    provincia: Mapped["Provincia"] = relationship(back_populates="ciudades")
