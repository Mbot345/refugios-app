from sqlalchemy import distinct, func, select
from sqlalchemy.orm import Session, contains_eager, joinedload, selectinload

from app.models.animal import Animal
from app.models.fundacion import Fundacion
from app.models.ubicacion import Ciudad

# Rangos de edad del filtro: clave -> (etiqueta, meses mínimos, meses máximos o None)
RANGOS_EDAD = {
    "cachorro": ("Menos de 1 año", 0, 11),
    "joven": ("1 a 2 años", 12, 35),
    "adulto": ("3 a 7 años", 36, 95),
    "senior": ("8 años o más", 96, None),
}


def listar_disponibles(db: Session, filtros: dict | None = None) -> list[Animal]:
    """Animales disponibles de fundaciones activas, con filtros opcionales."""
    filtros = filtros or {}
    consulta = (
        select(Animal)
        .join(Animal.fundacion)
        .options(contains_eager(Animal.fundacion))
        .where(Animal.estado == "disponible", Fundacion.activa.is_(True))
        .order_by(Animal.id.desc())
    )

    if filtros.get("especie"):
        consulta = consulta.where(Animal.especie == filtros["especie"])
    if filtros.get("tamano"):
        consulta = consulta.where(Animal.tamano == filtros["tamano"])
    if filtros.get("sexo"):
        consulta = consulta.where(Animal.sexo == filtros["sexo"])
    if filtros.get("raza"):
        consulta = consulta.where(Animal.raza.ilike(f"%{filtros['raza']}%"))

    rango = RANGOS_EDAD.get(filtros.get("edad", ""))
    if rango:
        _, minimo, maximo = rango
        consulta = consulta.where(Animal.edad_meses >= minimo)
        if maximo is not None:
            consulta = consulta.where(Animal.edad_meses <= maximo)

    return list(db.scalars(consulta).all())


def opciones_filtro(db: Session) -> dict[str, list[str]]:
    """Valores que existen hoy entre los animales disponibles, para llenar los filtros."""
    opciones = {}
    for columna in ("especie", "tamano", "sexo"):
        campo = getattr(Animal, columna)
        consulta = (
            select(distinct(campo))
            .join(Animal.fundacion)
            .where(
                Animal.estado == "disponible",
                Fundacion.activa.is_(True),
                campo.is_not(None),
            )
            .order_by(campo)
        )
        opciones[columna] = list(db.scalars(consulta).all())
    return opciones


def obtener_ficha(db: Session, animal_id: int) -> Animal | None:
    """Ficha pública: cualquier animal de una fundación activa (el estado se muestra en la ficha)."""
    consulta = (
        select(Animal)
        .join(Animal.fundacion)
        .options(
            contains_eager(Animal.fundacion),
            selectinload(Animal.fotos),
            selectinload(Animal.registros_sanitarios),
        )
        .where(Animal.id == animal_id, Fundacion.activa.is_(True))
    )
    return db.scalar(consulta)


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