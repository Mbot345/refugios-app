from datetime import date, time, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session, contains_eager, joinedload

from app.core.fechas import hoy
from app.models.evento import Evento
from app.models.fundacion import Fundacion
from app.models.user import User


# ---------- Consultas ----------
def listar_de_fundacion(db: Session, fundacion_id: int) -> list[Evento]:
    consulta = (
        select(Evento)
        .where(Evento.fundacion_id == fundacion_id)
        .order_by(Evento.fecha.desc(), Evento.id.desc())
    )
    return list(db.scalars(consulta).all())


def obtener_de_fundacion(db: Session, evento_id: int, fundacion_id: int) -> Evento | None:
    evento = db.get(Evento, evento_id)
    if evento is None or evento.fundacion_id != fundacion_id:
        return None
    return evento


def listar_publicos(db: Session, pasados: bool = False) -> list[Evento]:
    """Eventos de fundaciones activas: próximos (por defecto) o ya realizados."""
    consulta = (
        select(Evento)
        .join(Evento.fundacion)
        .options(contains_eager(Evento.fundacion))
        .where(Fundacion.activa.is_(True))
    )
    if pasados:
        consulta = consulta.where(Evento.fecha < hoy()).order_by(
            Evento.fecha.desc(), Evento.id.desc()
        )
    else:
        consulta = consulta.where(Evento.fecha >= hoy()).order_by(
            Evento.fecha.asc(), Evento.hora.asc(), Evento.id.asc()
        )
    return list(db.scalars(consulta).all())


def obtener_publico(db: Session, evento_id: int) -> Evento | None:
    consulta = (
        select(Evento)
        .join(Evento.fundacion)
        .options(contains_eager(Evento.fundacion))
        .where(Evento.id == evento_id, Fundacion.activa.is_(True))
    )
    return db.scalar(consulta)


def listar_todos(db: Session) -> list[Evento]:
    """Todos los eventos (supervisión de administrador y moderador)."""
    consulta = (
        select(Evento)
        .options(joinedload(Evento.fundacion))
        .order_by(Evento.fecha.desc(), Evento.id.desc())
    )
    return list(db.scalars(consulta).all())


# ---------- Datos del formulario ----------
def limpiar_datos(titulo: str, descripcion: str, fecha: str, hora: str, lugar: str) -> dict:
    return {
        "titulo": " ".join(titulo.split()),
        "descripcion": descripcion.strip(),
        "fecha": fecha.strip(),
        "hora": hora.strip(),
        "lugar": " ".join(lugar.split()),
    }


def a_datos(evento: Evento) -> dict:
    return {
        "titulo": evento.titulo,
        "descripcion": evento.descripcion,
        "fecha": evento.fecha.isoformat(),
        "hora": evento.hora.strftime("%H:%M") if evento.hora else "",
        "lugar": evento.lugar,
    }


def _parsear_fecha(texto: str) -> date | None:
    try:
        return date.fromisoformat(texto)  # el campo de fecha envía aaaa-mm-dd
    except ValueError:
        return None


def _parsear_hora(texto: str) -> time | None:
    try:
        return time.fromisoformat(texto)  # el campo de hora envía HH:MM
    except ValueError:
        return None


def validar(user: User, datos: dict) -> list[str]:
    errores = []

    if not user.fundacion.activa:
        errores.append("Tu fundación está suspendida: solo puedes consultar la información.")

    if not 5 <= len(datos["titulo"]) <= 120:
        errores.append("El título debe tener entre 5 y 120 caracteres.")
    if not 10 <= len(datos["descripcion"]) <= 2000:
        errores.append("La descripción debe tener entre 10 y 2000 caracteres.")

    fecha = _parsear_fecha(datos["fecha"])
    if fecha is None:
        errores.append("La fecha no es válida.")
    elif fecha < hoy():
        errores.append("La fecha del evento no puede ser anterior a hoy.")
    elif fecha > hoy() + timedelta(days=730):
        errores.append("La fecha del evento no puede superar los 2 años desde hoy.")

    if datos["hora"] and _parsear_hora(datos["hora"]) is None:
        errores.append("La hora no es válida (formato HH:MM).")

    if not 5 <= len(datos["lugar"]) <= 200:
        errores.append("El lugar debe tener entre 5 y 200 caracteres.")

    return errores


# ---------- Reglas de estado ----------
def motivo_no_editable(evento: Evento) -> str | None:
    if evento.estado == "cancelado":
        return "Un evento cancelado no se puede editar."
    if evento.es_pasado:
        return "Un evento que ya pasó no se puede editar."
    return None


def motivo_no_cancelable(evento: Evento) -> str | None:
    if evento.estado == "cancelado":
        return "Este evento ya está cancelado."
    if evento.es_pasado:
        return "Un evento que ya pasó no se puede cancelar."
    return None


# ---------- Escritura ----------
def _asignar(evento: Evento, datos: dict) -> None:
    evento.titulo = datos["titulo"]
    evento.descripcion = datos["descripcion"]
    evento.fecha = _parsear_fecha(datos["fecha"])
    evento.hora = _parsear_hora(datos["hora"]) if datos["hora"] else None
    evento.lugar = datos["lugar"]


def crear(db: Session, user: User, datos: dict) -> Evento:
    evento = Evento(estado="programado", fundacion_id=user.fundacion_id, creado_por=user.id)
    _asignar(evento, datos)
    db.add(evento)
    db.commit()
    db.refresh(evento)
    return evento


def actualizar(db: Session, evento: Evento, datos: dict) -> Evento:
    _asignar(evento, datos)
    db.commit()
    db.refresh(evento)
    return evento


def cancelar(db: Session, user: User, evento: Evento, motivo: str) -> list[str]:
    """Cancela el evento. Devuelve la lista de errores (vacía si se canceló)."""
    motivo = " ".join(motivo.split())
    errores = []

    if not user.fundacion.activa:
        errores.append("Tu fundación está suspendida: solo puedes consultar la información.")
    razon = motivo_no_cancelable(evento)
    if razon:
        errores.append(razon)
    if not 5 <= len(motivo) <= 300:
        errores.append("Escribe el motivo de la cancelación (entre 5 y 300 caracteres).")
    if errores:
        return errores

    evento.estado = "cancelado"
    evento.motivo_cancelacion = motivo
    db.commit()
    return []