from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.core.constants import ESPECIES, SEXOS, TAMANOS
from app.models.animal import Animal
from app.models.fundacion import Fundacion
from app.models.user import User


def _es_trabajador(user: User) -> bool:
    return user.rol == "trabajador"


def listar(db: Session, user: User) -> list[Animal]:
    consulta = (
        select(Animal)
        .options(joinedload(Animal.fundacion))
        .order_by(Animal.id.desc())
    )
    if _es_trabajador(user):
        consulta = consulta.where(Animal.fundacion_id == user.fundacion_id)
    return list(db.scalars(consulta).all())


def obtener(db: Session, animal_id: int, user: User) -> Animal | None:
    """Devuelve el animal solo si el usuario puede gestionarlo."""
    animal = db.get(Animal, animal_id)
    if animal is None:
        return None
    if _es_trabajador(user) and animal.fundacion_id != user.fundacion_id:
        return None
    return animal


def listar_fundaciones(db: Session, user: User) -> list[Fundacion]:
    """Fundaciones que el usuario puede elegir: el admin todas las activas, el trabajador la suya."""
    consulta = select(Fundacion).where(Fundacion.activa.is_(True)).order_by(Fundacion.nombre)
    if _es_trabajador(user):
        consulta = consulta.where(Fundacion.id == user.fundacion_id)
    return list(db.scalars(consulta).all())


def limpiar_datos(
    nombre: str,
    especie: str,
    raza: str,
    sexo: str,
    tamano: str,
    edad_meses: str,
    estado_salud: str,
    descripcion: str,
    fundacion_id: str,
) -> dict:
    """Quita espacios sobrantes y convierte los vacíos en None."""
    return {
        "nombre": nombre.strip(),
        "especie": especie,
        "raza": raza.strip() or None,
        "sexo": sexo,
        "tamano": tamano,
        "edad_meses": edad_meses.strip() or None,
        "estado_salud": estado_salud.strip(),
        "descripcion": descripcion.strip() or None,
        "fundacion_id": fundacion_id.strip(),
    }


def a_datos(animal: Animal) -> dict:
    """Convierte un animal en el diccionario que usa el formulario de edición."""
    return {
        "nombre": animal.nombre,
        "especie": animal.especie,
        "raza": animal.raza or "",
        "sexo": animal.sexo,
        "tamano": animal.tamano,
        "edad_meses": "" if animal.edad_meses is None else str(animal.edad_meses),
        "estado_salud": animal.estado_salud,
        "descripcion": animal.descripcion or "",
        "fundacion_id": str(animal.fundacion_id),
    }


def validar(db: Session, user: User, datos: dict) -> list[str]:
    """Devuelve la lista de errores. Si está vacía, los datos son válidos."""
    errores = []

    if not 2 <= len(datos["nombre"]) <= 80:
        errores.append("El nombre debe tener entre 2 y 80 caracteres.")
    if datos["raza"] and len(datos["raza"]) > 80:
        errores.append("La raza no puede superar los 80 caracteres.")
    if datos["especie"] not in ESPECIES:
        errores.append("Selecciona una especie válida.")
    if datos["sexo"] not in SEXOS:
        errores.append("Selecciona un sexo válido.")
    if datos["tamano"] not in TAMANOS:
        errores.append("Selecciona un tamaño válido.")

    if datos["edad_meses"] is not None:
        if not datos["edad_meses"].isdigit() or not 0 <= int(datos["edad_meses"]) <= 360:
            errores.append("La edad aproximada debe ser un número de meses entre 0 y 360.")

    if not 3 <= len(datos["estado_salud"]) <= 100:
        errores.append("El estado de salud debe tener entre 3 y 100 caracteres.")
    if datos["descripcion"] and len(datos["descripcion"]) > 2000:
        errores.append("La descripción no puede superar los 2000 caracteres.")

    # El trabajador siempre usa su propia fundación; el admin la elige de la lista
    if not _es_trabajador(user):
        fundacion = (
            db.get(Fundacion, int(datos["fundacion_id"]))
            if datos["fundacion_id"].isdigit()
            else None
        )
        if fundacion is None or not fundacion.activa:
            errores.append("Selecciona una fundación válida.")

    return errores


def _asignar(animal: Animal, datos: dict, user: User) -> None:
    animal.nombre = datos["nombre"]
    animal.especie = datos["especie"]
    animal.raza = datos["raza"]
    animal.sexo = datos["sexo"]
    animal.tamano = datos["tamano"]
    animal.edad_meses = int(datos["edad_meses"]) if datos["edad_meses"] else None
    animal.estado_salud = datos["estado_salud"]
    animal.descripcion = datos["descripcion"]
    if _es_trabajador(user):
        animal.fundacion_id = user.fundacion_id
    else:
        animal.fundacion_id = int(datos["fundacion_id"])
    # El estado NO se asigna aquí: solo cambia con el flujo de solicitudes


def crear(db: Session, user: User, datos: dict) -> Animal:
    animal = Animal()
    _asignar(animal, datos, user)
    db.add(animal)
    db.commit()
    db.refresh(animal)
    return animal


def actualizar(db: Session, user: User, animal: Animal, datos: dict) -> Animal:
    _asignar(animal, datos, user)
    db.commit()
    db.refresh(animal)
    return animal


def motivo_no_eliminable(animal: Animal) -> str | None:
    """Devuelve el motivo si el animal no se puede eliminar, o None si sí se puede."""
    if animal.solicitudes:
        return "No se puede eliminar: el animal tiene solicitudes registradas."
    return None


def eliminar(db: Session, animal: Animal) -> None:
    db.delete(animal)
    db.commit()