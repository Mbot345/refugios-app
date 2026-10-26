import re

from email_validator import EmailNotValidError, validate_email
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.models.fundacion import Fundacion
from app.models.ubicacion import Ciudad, Provincia

TELEFONO_EC = re.compile(r"^(09\d{8}|0[2-7]\d{7})$")


def listar(db: Session) -> list[Fundacion]:
    stmt = select(Fundacion).options(joinedload(Fundacion.ciudad).joinedload(Ciudad.provincia)).order_by(Fundacion.nombre)
    return list(db.scalars(stmt).all())


def obtener(db: Session, fundacion_id: int) -> Fundacion | None:
    return db.get(Fundacion, fundacion_id)


def listar_provincias(db: Session) -> list[Provincia]:
    return list(db.scalars(select(Provincia).order_by(Provincia.nombre)).all())


def ciudades_de(db: Session, provincia_id: int) -> list[Ciudad]:
    stmt = select(Ciudad).where(Ciudad.provincia_id == provincia_id).order_by(Ciudad.nombre)
    return list(db.scalars(stmt).all())


def limpiar_datos(nombre: str, descripcion: str, direccion: str, provincia_id: str,
                  ciudad_id: str, telefono: str, email_contacto: str) -> dict:
    return {"nombre": nombre.strip(), "descripcion": descripcion.strip() or None,
            "direccion": direccion.strip(), "provincia_id": provincia_id.strip(),
            "ciudad_id": ciudad_id.strip(), "telefono": re.sub(r"[\s\-]", "", telefono) or None,
            "email_contacto": email_contacto.strip().lower()}


def a_datos(f: Fundacion) -> dict:
    return {"nombre": f.nombre, "descripcion": f.descripcion or "", "direccion": f.direccion,
            "provincia_id": str(f.ciudad.provincia_id), "ciudad_id": str(f.ciudad_id),
            "telefono": f.telefono or "", "email_contacto": f.email_contacto}


def validar(db: Session, datos: dict, actual_id: int | None = None) -> list[str]:
    errores = []
    if not 3 <= len(datos["nombre"]) <= 100:
        errores.append("El nombre debe tener entre 3 y 100 caracteres.")
    elif db.scalar(select(Fundacion.id).where(func.lower(Fundacion.nombre) == datos["nombre"].lower(), Fundacion.id != (actual_id or 0))):
        errores.append("Ya existe una fundación con ese nombre.")
    if not 5 <= len(datos["direccion"]) <= 200:
        errores.append("La dirección debe tener entre 5 y 200 caracteres.")
    if datos["descripcion"] and len(datos["descripcion"]) > 1000:
        errores.append("La descripción no puede superar los 1000 caracteres.")
    try:
        validate_email(datos["email_contacto"], check_deliverability=False)
    except EmailNotValidError:
        errores.append("El correo de contacto no es válido.")
    if datos["telefono"] and not TELEFONO_EC.fullmatch(datos["telefono"]):
        errores.append("El teléfono no es válido: usa un celular (09XXXXXXXX) o un convencional (0 + código de área + 7 dígitos).")
    provincia = db.get(Provincia, int(datos["provincia_id"])) if datos["provincia_id"].isdigit() else None
    ciudad = db.get(Ciudad, int(datos["ciudad_id"])) if datos["ciudad_id"].isdigit() else None
    if provincia is None:
        errores.append("Selecciona una provincia válida.")
    elif ciudad is None:
        errores.append("Selecciona una ciudad válida.")
    elif ciudad.provincia_id != provincia.id:
        errores.append("La ciudad seleccionada no pertenece a la provincia elegida.")
    return errores


def _asignar(f: Fundacion, datos: dict) -> None:
    f.nombre, f.descripcion, f.direccion = datos["nombre"], datos["descripcion"], datos["direccion"]
    f.ciudad_id, f.telefono, f.email_contacto = int(datos["ciudad_id"]), datos["telefono"], datos["email_contacto"]


def crear(db: Session, datos: dict) -> Fundacion:
    f = Fundacion(activa=True)
    _asignar(f, datos); db.add(f); db.commit(); db.refresh(f)
    return f


def actualizar(db: Session, f: Fundacion, datos: dict) -> Fundacion:
    _asignar(f, datos); db.commit(); db.refresh(f)
    return f


def cambiar_activa(db: Session, f: Fundacion) -> None:
    f.activa = not f.activa; db.commit()
