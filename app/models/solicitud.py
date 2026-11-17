from datetime import date, datetime
from typing import Optional

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Index, String, Text, func, text
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

    # Datos personales
    nombres_completos: Mapped[str] = mapped_column(String(120))
    cedula: Mapped[str] = mapped_column(String(10))
    fecha_nacimiento: Mapped[date] = mapped_column(Date)
    telefono_convencional: Mapped[Optional[str]] = mapped_column(String(20))
    telefono_movil: Mapped[str] = mapped_column(String(20))
    direccion_vivienda: Mapped[str] = mapped_column(String(200))
    ocupacion: Mapped[str] = mapped_column(String(100))

    # Domicilio
    tipo_vivienda: Mapped[str] = mapped_column(String(20))
    metros_vivienda: Mapped[int] = mapped_column()
    metros_area_verde: Mapped[int] = mapped_column()
    dimension_area_comunal: Mapped[Optional[str]] = mapped_column(String(100))
    tenencia_vivienda: Mapped[str] = mapped_column(String(20))

    # Motivos para adoptar
    motivo_adopcion: Mapped[str] = mapped_column(Text)
    acepta_visitas: Mapped[bool] = mapped_column(Boolean)
    experiencia_previa: Mapped[Optional[str]] = mapped_column(Text)

    # Revisión
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