from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.mascota import Mascota
from app.models.refugio import Refugio

ESPECIES = ["Perro", "Gato", "Otro"]
SEXOS = ["Macho", "Hembra"]
ESTADOS = ["disponible", "en_proceso", "adoptada"]


def listar(db: Session) -> list[Mascota]:
    consulta = select(Mascota).options(joinedload(Mascota.refugio)).order_by(Mascota.id.desc())
    return list(db.scalars(consulta).all())


def obtener(db: Session, mascota_id: int) -> Mascota | None:
    return db.get(Mascota, mascota_id)


def listar_refugios(db: Session) -> list[Refugio]:
    return list(db.scalars(select(Refugio).order_by(Refugio.nombre)).all())


def limpiar_datos(
    nombre: str, especie: str, raza: str, sexo: str, fecha_nacimiento: str,
    descripcion: str, estado: str, refugio_id: str,
) -> dict:
    return {
        "nombre": nombre.strip(), "especie": especie, "raza": raza.strip() or None,
        "sexo": sexo, "fecha_nacimiento": fecha_nacimiento.strip() or None,
        "descripcion": descripcion.strip() or None, "estado": estado,
        "refugio_id": refugio_id.strip(),
    }


def a_datos(mascota: Mascota) -> dict:
    return {
        "nombre": mascota.nombre, "especie": mascota.especie,
        "raza": mascota.raza or "", "sexo": mascota.sexo,
        "fecha_nacimiento": mascota.fecha_nacimiento.isoformat() if mascota.fecha_nacimiento else "",
        "descripcion": mascota.descripcion or "", "estado": mascota.estado,
        "refugio_id": str(mascota.refugio_id),
    }


def validar(db: Session, datos: dict) -> list[str]:
    errores = []
    if not 2 <= len(datos["nombre"]) <= 80:
        errores.append("El nombre debe tener entre 2 y 80 caracteres.")
    if datos["raza"] and len(datos["raza"]) > 80:
        errores.append("La raza no puede superar los 80 caracteres.")
    if datos["especie"] not in ESPECIES:
        errores.append("Selecciona una especie válida.")
    if datos["sexo"] not in SEXOS:
        errores.append("Selecciona un sexo válido.")
    if datos["estado"] not in ESTADOS:
        errores.append("Selecciona un estado válido.")
    if datos["fecha_nacimiento"]:
        try:
            fecha = date.fromisoformat(datos["fecha_nacimiento"])
            if fecha > date.today():
                errores.append("La fecha de nacimiento no puede ser futura.")
        except ValueError:
            errores.append("La fecha de nacimiento no es válida.")
    refugio_id = datos["refugio_id"]
    if not refugio_id.isdigit() or db.get(Refugio, int(refugio_id)) is None:
        errores.append("Selecciona un refugio válido.")
    return errores


def _asignar(mascota: Mascota, datos: dict) -> None:
    mascota.nombre = datos["nombre"]
    mascota.especie = datos["especie"]
    mascota.raza = datos["raza"]
    mascota.sexo = datos["sexo"]
    mascota.fecha_nacimiento = date.fromisoformat(datos["fecha_nacimiento"]) if datos["fecha_nacimiento"] else None
    mascota.descripcion = datos["descripcion"]
    mascota.estado = datos["estado"]
    mascota.refugio_id = int(datos["refugio_id"])


def crear(db: Session, datos: dict) -> Mascota:
    mascota = Mascota()
    _asignar(mascota, datos)
    db.add(mascota)
    db.commit()
    db.refresh(mascota)
    return mascota


def actualizar(db: Session, mascota: Mascota, datos: dict) -> Mascota:
    _asignar(mascota, datos)
    db.commit()
    db.refresh(mascota)
    return mascota


def eliminar(db: Session, mascota: Mascota) -> None:
    db.delete(mascota)
    db.commit()
