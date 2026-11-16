from sqlalchemy import func, select
from sqlalchemy.orm import Session, contains_eager, joinedload

from app.models.animal import Animal
from app.models.fundacion import Fundacion
from app.models.ubicacion import Ciudad


def listar_disponibles(db: Session) -> list[Animal]:
    """Animales disponibles de fundaciones activas (lo único que ve el público)."""
    consulta = (
        select(Animal)
        .join(Animal.fundacion)
        .options(contains_eager(Animal.fundacion))
        .where(Animal.estado == "disponible", Fundacion.activa.is_(True))
        .order_by(Animal.id.desc())
    )
    return list(db.scalars(consulta).all())


def listar_fundaciones_activas(db: Session) -> list[Fundacion]:
    consulta = (
        select(Fundacion)
        .options(joinedload(Fundacion.ciudad).joinedload(Ciudad.provincia))
        .where(Fundacion.activa.is_(True))
        .order_by(Fundacion.nombre)
    )
    return list(db.scalars(consulta).all())


def conteo_disponibles(db: Session) -> dict[int, int]:
    """Cantidad de animales disponibles por fundación: {fundacion_id: total}."""
    filas = db.execute(
        select(Animal.fundacion_id, func.count())
        .where(Animal.estado == "disponible")
        .group_by(Animal.fundacion_id)
    ).all()
    return {fundacion_id: total for fundacion_id, total in filas}