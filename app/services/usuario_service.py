from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.core.constants import ROLES
from app.models.fundacion import Fundacion
from app.models.user import User


def listar(db: Session) -> list[User]:
    return list(db.scalars(select(User).options(joinedload(User.fundacion)).order_by(User.id)).all())


def obtener(db: Session, usuario_id: int) -> User | None:
    return db.get(User, usuario_id)


def listar_fundaciones_activas(db: Session) -> list[Fundacion]:
    return list(db.scalars(select(Fundacion).where(Fundacion.activa.is_(True)).order_by(Fundacion.nombre)).all())


def validar_cambios(db: Session, admin: User, usuario: User, rol: str, fundacion_id: str) -> list[str]:
    errores = []
    if rol not in ROLES:
        errores.append("Selecciona un rol válido.")
    if usuario.id == admin.id and rol != "admin":
        errores.append("No puedes quitarte a ti mismo el rol de administrador.")
    if rol == "trabajador":
        f = db.get(Fundacion, int(fundacion_id)) if fundacion_id.isdigit() else None
        if f is None or not f.activa:
            errores.append("Un trabajador debe estar asociado a una fundación activa.")
    return errores


def aplicar_cambios(db: Session, usuario: User, rol: str, fundacion_id: str) -> None:
    usuario.rol = rol
    usuario.fundacion_id = int(fundacion_id) if rol == "trabajador" else None
    db.commit()


def cambiar_estado(db: Session, admin: User, usuario: User) -> str | None:
    if usuario.id == admin.id:
        return "No puedes desactivar tu propia cuenta."
    usuario.activo = not usuario.activo; db.commit()
    return None
