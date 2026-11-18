from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, contains_eager, joinedload, selectinload

from app.core.constants import ESTADOS_SOLICITUD
from app.models.animal import Animal
from app.models.solicitud import HistorialSolicitud, SolicitudPreadopcion
from app.models.user import User

MOTIVO_AUTOMATICO = "Se aprobó otra solicitud para este animal"


class ReglaNegocio(Exception):
    """Una regla impide la acción. El mensaje se muestra a la persona usuaria."""


# ---------- Consultas ----------
def _base(fundacion_id: int):
    return (
        select(SolicitudPreadopcion)
        .join(SolicitudPreadopcion.animal)
        .options(contains_eager(SolicitudPreadopcion.animal))
        .where(Animal.fundacion_id == fundacion_id)
    )


def listar_de_fundacion(
    db: Session, fundacion_id: int, estado: str = ""
) -> list[SolicitudPreadopcion]:
    consulta = _base(fundacion_id).order_by(SolicitudPreadopcion.fecha_solicitud.desc())
    if estado in ESTADOS_SOLICITUD:
        consulta = consulta.where(SolicitudPreadopcion.estado == estado)
    return list(db.scalars(consulta).all())


def obtener_de_fundacion(
    db: Session, solicitud_id: int, fundacion_id: int
) -> SolicitudPreadopcion | None:
    """Solo devuelve solicitudes de animales de la fundación indicada."""
    consulta = _base(fundacion_id).options(
        joinedload(SolicitudPreadopcion.solicitante),
        selectinload(SolicitudPreadopcion.historial),
    ).where(SolicitudPreadopcion.id == solicitud_id)
    return db.scalar(consulta)


# ---------- Utilidades internas ----------
def _limpiar_observacion(texto: str, obligatoria: bool) -> str | None:
    texto = " ".join(texto.split())
    if obligatoria and len(texto) < 5:
        raise ReglaNegocio("Escribe una observación de al menos 5 caracteres.")
    if len(texto) > 500:
        raise ReglaNegocio("La observación no puede superar los 500 caracteres.")
    return texto or None


def _exigir_fundacion_activa(user: User) -> None:
    if not user.fundacion.activa:
        raise ReglaNegocio("Tu fundación está suspendida: solo puedes consultar la información.")


def _bloquear(db: Session, solicitud: SolicitudPreadopcion) -> Animal:
    """Bloquea el animal y relee la solicitud, para decidir con datos actuales."""
    animal = db.scalar(
        select(Animal)
        .where(Animal.id == solicitud.animal_id)
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    db.refresh(solicitud)
    return animal


def _registrar(
    solicitud: SolicitudPreadopcion, nuevo: str, user: User, observacion: str | None
) -> None:
    solicitud.historial.append(
        HistorialSolicitud(
            estado_anterior=solicitud.estado,
            estado_nuevo=nuevo,
            observacion=observacion,
            usuario_id=user.id,
        )
    )
    solicitud.estado = nuevo


def _resolver(
    solicitud: SolicitudPreadopcion, nuevo: str, user: User, observacion: str | None
) -> None:
    """Cambio hecho por el personal de la fundación: queda quién y cuándo lo revisó."""
    _registrar(solicitud, nuevo, user, observacion)
    solicitud.observacion_revision = observacion
    solicitud.fecha_revision = datetime.now(timezone.utc)
    solicitud.revisada_por = user.id


def _guardar(db: Session) -> None:
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise ReglaNegocio(
            "Otra persona modificó este animal al mismo tiempo. Recarga la página e inténtalo de nuevo."
        )


def _cargar(db: Session, user: User, solicitud_id: int) -> SolicitudPreadopcion:
    solicitud = obtener_de_fundacion(db, solicitud_id, user.fundacion_id)
    if solicitud is None:
        raise ReglaNegocio("La solicitud no existe.")
    return solicitud


# ---------- Acciones del personal ----------
def aprobar(db: Session, user: User, solicitud_id: int, observacion: str
            ) -> tuple[SolicitudPreadopcion, list[SolicitudPreadopcion]]:
    observacion = _limpiar_observacion(observacion, obligatoria=False)
    solicitud = _cargar(db, user, solicitud_id)
    animal = _bloquear(db, solicitud)

    if solicitud.estado != "pendiente":
        raise ReglaNegocio("Solo se puede aprobar una solicitud pendiente.")
    if animal.estado != "disponible":
        raise ReglaNegocio("El animal ya no está disponible.")

    _resolver(solicitud, "aprobada", user, observacion)
    animal.estado = "en_proceso"

    # Las demás solicitudes pendientes del mismo animal se rechazan automáticamente
    otras = db.scalars(
        select(SolicitudPreadopcion).where(
            SolicitudPreadopcion.animal_id == animal.id,
            SolicitudPreadopcion.estado == "pendiente",
            SolicitudPreadopcion.id != solicitud.id,
        )
    ).all()
    for otra in otras:
        _resolver(otra, "rechazada", user, MOTIVO_AUTOMATICO)

    _guardar(db)
    return solicitud, list(otras)


def rechazar(db: Session, user: User, solicitud_id: int, observacion: str) -> SolicitudPreadopcion:
    _exigir_fundacion_activa(user)
    observacion = _limpiar_observacion(observacion, obligatoria=True)
    solicitud = _cargar(db, user, solicitud_id)
    _bloquear(db, solicitud)

    if solicitud.estado != "pendiente":
        raise ReglaNegocio("Solo se puede rechazar una solicitud pendiente.")

    _resolver(solicitud, "rechazada", user, observacion)
    _guardar(db)
    return solicitud


def revocar(db: Session, user: User, solicitud_id: int, observacion: str) -> SolicitudPreadopcion:
    """Deja sin efecto una aprobada: la solicitud queda cancelada y el animal vuelve a disponible."""
    _exigir_fundacion_activa(user)
    observacion = _limpiar_observacion(observacion, obligatoria=True)
    solicitud = _cargar(db, user, solicitud_id)
    animal = _bloquear(db, solicitud)

    if solicitud.estado != "aprobada":
        raise ReglaNegocio("Solo se puede revocar una solicitud aprobada.")

    _resolver(solicitud, "cancelada", user, observacion)
    animal.estado = "disponible"
    _guardar(db)
    return solicitud


def finalizar(db: Session, user: User, solicitud_id: int, observacion: str) -> SolicitudPreadopcion:
    """Confirma la adopción definitiva: la solicitud queda finalizada y el animal, adoptado."""
    _exigir_fundacion_activa(user)
    observacion = _limpiar_observacion(observacion, obligatoria=False)
    solicitud = _cargar(db, user, solicitud_id)
    animal = _bloquear(db, solicitud)

    if solicitud.estado != "aprobada":
        raise ReglaNegocio("Solo se puede confirmar la adopción de una solicitud aprobada.")

    _resolver(solicitud, "finalizada", user, observacion)
    animal.estado = "adoptado"
    _guardar(db)
    return solicitud


# ---------- Acción del adoptante ----------
def cancelar_propia(db: Session, user: User, solicitud_id: int) -> SolicitudPreadopcion:
    """El adoptante cancela su solicitud mientras esté pendiente o aprobada."""
    solicitud = db.scalar(
        select(SolicitudPreadopcion).where(
            SolicitudPreadopcion.id == solicitud_id,
            SolicitudPreadopcion.usuario_id == user.id,
        )
    )
    if solicitud is None:
        raise ReglaNegocio("La solicitud no existe.")

    animal = _bloquear(db, solicitud)
    if solicitud.estado not in ("pendiente", "aprobada"):
        raise ReglaNegocio("Esta solicitud ya no se puede cancelar.")

    estaba_aprobada = solicitud.estado == "aprobada"
    _registrar(solicitud, "cancelada", user, "Cancelada por el solicitante")
    if estaba_aprobada:
        animal.estado = "disponible"

    _guardar(db)
    return solicitud