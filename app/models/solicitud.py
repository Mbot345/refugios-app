from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Index, String, Text, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class SolicitudPreadopcion(Base):
    __tablename__ = "solicitudes_preadopcion"
    __table_args__ = (
        # Un usuario no puede tener dos solicitudes pendientes para el mismo animal
        Index(
            "uq_solicitud_pendiente_usuario_animal",
            "animal_id", "usuario_id",
            unique=True,
            postgresql_where=text("estado = 'pendiente'"),
        ),
        # Un animal no puede tener dos solicitudes aprobadas/finalizadas a la vez
        Index(
            "uq_solicitud_activa_por_animal",
            "animal_id",
            unique=True,
            postgresql_where=text("estado IN ('aprobada', 'finalizada')"),
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    estado: Mapped[str] = mapped_column(String(20), default="pendiente")
    telefono: Mapped[str] = mapped_column(String(20))
    domicilio: Mapped[str] = mapped_column(String(200))
    experiencia_previa: Mapped[str] = mapped_column(Text)
    condiciones_cuidado: Mapped[str] = mapped_column(Text)
    observacion_revision: Mapped[Optional[str]] = mapped_column(Text)
    fecha_solicitud: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    fecha_revision: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    animal_id: Mapped[int] = mapped_column(ForeignKey("animales.id"))
    usuario_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    revisada_por: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))

    animal: Mapped["Animal"] = relationship(back_populates="solicitudes")
    solicitante: Mapped["User"] = relationship(foreign_keys="SolicitudPreadopcion.usuario_id")
    revisor: Mapped[Optional["User"]] = relationship(
        foreign_keys="SolicitudPreadopcion.revisada_por"
    )
    historial: Mapped[list["HistorialSolicitud"]] = relationship(
        back_populates="solicitud",
        cascade="all, delete-orphan",
        order_by="HistorialSolicitud.fecha",
    )


class HistorialSolicitud(Base):
    __tablename__ = "historial_solicitud"

    id: Mapped[int] = mapped_column(primary_key=True)
    estado_anterior: Mapped[Optional[str]] = mapped_column(String(20))
    estado_nuevo: Mapped[str] = mapped_column(String(20))
    observacion: Mapped[Optional[str]] = mapped_column(Text)
    fecha: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    solicitud_id: Mapped[int] = mapped_column(ForeignKey("solicitudes_preadopcion.id"))
    usuario_id: Mapped[int] = mapped_column(ForeignKey("users.id"))

    solicitud: Mapped["SolicitudPreadopcion"] = relationship(back_populates="historial")