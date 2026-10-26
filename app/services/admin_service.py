from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.constants import ESTADOS_ANIMAL, ESTADOS_SOLICITUD
from app.models.animal import Animal
from app.models.fundacion import Fundacion
from app.models.solicitud import SolicitudPreadopcion
from app.models.user import User


def _conteo(db: Session, columna, estados: tuple) -> dict:
    filas = db.execute(select(columna, func.count()).group_by(columna)).all()
    contados = {estado: total for estado, total in filas}
    return {estado: contados.get(estado, 0) for estado in estados}


def estadisticas(db: Session) -> dict:
    actividad = db.execute(select(Fundacion.nombre, Fundacion.activa,
        func.count(func.distinct(Animal.id)), func.count(func.distinct(SolicitudPreadopcion.id)))
        .select_from(Fundacion).outerjoin(Animal, Animal.fundacion_id == Fundacion.id)
        .outerjoin(SolicitudPreadopcion, SolicitudPreadopcion.animal_id == Animal.id)
        .group_by(Fundacion.id).order_by(Fundacion.nombre)).all()
    return {"animales": _conteo(db, Animal.estado, ESTADOS_ANIMAL),
        "solicitudes": _conteo(db, SolicitudPreadopcion.estado, ESTADOS_SOLICITUD),
        "actividad": [{"fundacion": n, "activa": a, "animales": an, "solicitudes": s} for n, a, an, s in actividad],
        "usuarios_total": db.scalar(select(func.count()).select_from(User)),
        "usuarios_activos": db.scalar(select(func.count()).select_from(User).where(User.activo.is_(True)))}
