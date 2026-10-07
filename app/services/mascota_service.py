from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.mascota import Mascota
from app.models.refugio import Refugio
from app.schemas.mascota import MascotaData


def obtener_mascotas(db: Session) -> list[Mascota]:
    return list(db.scalars(select(Mascota).options(selectinload(Mascota.refugio)).order_by(Mascota.id)))


def obtener_mascota(db: Session, mascota_id: int) -> Mascota | None:
    return db.scalar(
        select(Mascota).options(selectinload(Mascota.refugio)).where(Mascota.id == mascota_id)
    )


def obtener_refugios(db: Session) -> list[Refugio]:
    return list(db.scalars(select(Refugio).order_by(Refugio.nombre)))


def crear_mascota(db: Session, datos: MascotaData) -> Mascota:
    mascota = Mascota(**datos.model_dump())
    db.add(mascota)
    db.commit()
    db.refresh(mascota)
    return mascota


def actualizar_mascota(db: Session, mascota: Mascota, datos: MascotaData) -> Mascota:
    for campo, valor in datos.model_dump().items():
        setattr(mascota, campo, valor)
    db.commit()
    db.refresh(mascota)
    return mascota


def eliminar_mascota(db: Session, mascota: Mascota) -> None:
    db.delete(mascota)
    db.commit()
