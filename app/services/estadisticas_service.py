from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.constants import ESTADOS_ANIMAL, ESTADOS_SOLICITUD
from app.core.fechas import hoy
from app.models.animal import Animal
from app.models.evento import Evento
from app.models.solicitud import SolicitudPreadopcion


def _filas(conteos: dict, estados) -> list[dict]:
    """Una fila por estado (aunque tenga 0), con su porcentaje del total para las barras."""
    total = sum(conteos.values())
    return [
        {
            "estado": estado,
            "total": conteos.get(estado, 0),
            "porcentaje": round(conteos.get(estado, 0) * 100 / total) if total else 0,
        }
        for estado in estados
    ]


def de_fundacion(db: Session, fundacion_id: int) -> dict:
    """Resumen de una fundación: animales, solicitudes y eventos."""
    animales = dict(
        db.execute(
            select(Animal.estado, func.count())
            .where(Animal.fundacion_id == fundacion_id)
            .group_by(Animal.estado)
        ).all()
    )
    solicitudes = dict(
        db.execute(
            select(SolicitudPreadopcion.estado, func.count())
            .join(SolicitudPreadopcion.animal)
            .where(Animal.fundacion_id == fundacion_id)
            .group_by(SolicitudPreadopcion.estado)
        ).all()
    )
    eventos_proximos = db.scalar(
        select(func.count())
        .select_from(Evento)
        .where(
            Evento.fundacion_id == fundacion_id,
            Evento.estado == "programado",
            Evento.fecha >= hoy(),
        )
    )

    return {
        "animales": _filas(animales, ESTADOS_ANIMAL),
        "solicitudes": _filas(solicitudes, ESTADOS_SOLICITUD),
        "total_animales": sum(animales.values()),
        "total_solicitudes": sum(solicitudes.values()),
        "por_revisar": solicitudes.get("pendiente", 0),
        "adopciones": solicitudes.get("finalizada", 0),
        "eventos_proximos": eventos_proximos,
    }