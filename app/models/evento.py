from datetime import date, datetime, time
from typing import Optional

from sqlalchemy import Date, DateTime, ForeignKey, String, Text, Time, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.core.fechas import hoy


class Evento(Base):
    __tablename__ = "eventos"

    id: Mapped[int] = mapped_column(primary_key=True)
    titulo: Mapped[str] = mapped_column(String(120))
    descripcion: Mapped[str] = mapped_column(Text)
    fecha: Mapped[date] = mapped_column(Date)
    hora: Mapped[Optional[time]] = mapped_column(Time)
    lugar: Mapped[str] = mapped_column(String(200))
    estado: Mapped[str] = mapped_column(String(20), default="programado")  # programado | cancelado
    motivo_cancelacion: Mapped[Optional[str]] = mapped_column(Text)
    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    fundacion_id: Mapped[int] = mapped_column(ForeignKey("fundaciones.id"))
    creado_por: Mapped[int] = mapped_column(ForeignKey("users.id"))

    fundacion: Mapped["Fundacion"] = relationship()

    @property
    def es_pasado(self) -> bool:
        return self.fecha < hoy()

    @property
    def estado_visible(self) -> str:
        """programado, cancelado o finalizado (este último se calcula, no se guarda)."""
        if self.estado == "cancelado":
            return "cancelado"
        return "finalizado" if self.es_pasado else "programado"