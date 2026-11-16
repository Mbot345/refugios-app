from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.constants import ROLES_FUNDACION
from app.models.user import User


def listar_equipo(db: Session, fundacion_id: int) -> list[User]:
    consulta = select(User).where(User.fundacion_id == fundacion_id).order_by(User.username)
    return list(db.scalars(consulta).all())


def obtener_miembro(db: Session, fundacion_id: int, usuario_id: int) -> User | None:
    """Devuelve el usuario solo si pertenece a esa fundación."""
    usuario = db.get(User, usuario_id)
    if usuario is None or usuario.fundacion_id != fundacion_id:
        return None
    return usuario


def validar_alta(
    db: Session, identificador: str, rol: str
) -> tuple[User | None, list[str]]:
    """Solo se pueden sumar usuarios registrados, activos y sin fundación ni rol de plataforma."""
    errores = []
    identificador = identificador.strip().lower()

    if rol not in ROLES_FUNDACION:
        errores.append("Selecciona un rol válido para la fundación.")

    candidato = None
    if identificador:
        candidato = db.scalar(
            select(User).where(
                or_(
                    func.lower(User.username) == identificador,
                    func.lower(User.email) == identificador,
                )
            )
        )
    if (
        candidato is None
        or not candidato.activo
        or candidato.rol != "adoptante"
        or candidato.fundacion_id is not None
    ):
        errores.append(
            "No se encontró un usuario disponible con ese usuario o correo. "
            "Debe estar registrado, activo y sin fundación asignada."
        )
        candidato = None

    return candidato, errores


def asignar(db: Session, usuario: User, rol: str, fundacion_id: int) -> None:
    usuario.rol = rol
    usuario.fundacion_id = fundacion_id
    db.commit()


def validar_cambio(admin: User, miembro: User, rol: str) -> list[str]:
    errores = []
    if rol not in ROLES_FUNDACION:
        errores.append("Selecciona un rol válido para la fundación.")
    if miembro.id == admin.id:
        errores.append("No puedes cambiar tu propio rol.")
    return errores


def cambiar_rol(db: Session, miembro: User, rol: str) -> None:
    miembro.rol = rol
    db.commit()


def validar_quitar(admin: User, miembro: User) -> str | None:
    if miembro.id == admin.id:
        return "No puedes quitarte a ti mismo del equipo."
    return None


def quitar(db: Session, miembro: User) -> None:
    miembro.rol = "adoptante"
    miembro.fundacion_id = None
    db.commit()