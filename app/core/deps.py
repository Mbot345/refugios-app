from fastapi import Depends, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User


class NotAuthenticated(Exception):
    """Se lanza cuando se intenta entrar sin sesión válida."""


class Forbidden(Exception):
    """Se lanza cuando el usuario tiene sesión pero no el rol necesario."""

    def __init__(self, message: str = "No tienes permiso para acceder a esa sección."):
        self.message = message
        super().__init__(message)


def get_optional_user(request: Request, db: Session = Depends(get_db)) -> User | None:
    """Devuelve el usuario si hay sesión, o None. Para páginas públicas."""
    user_id = request.session.get("user_id")
    if not user_id:
        return None
    user = db.get(User, user_id)
    if user is None or not user.activo:
        return None
    return user


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    user_id = request.session.get("user_id")
    if not user_id:
        raise NotAuthenticated()

    user = db.get(User, user_id)
    if user is None or not user.activo:
        request.session.clear()
        raise NotAuthenticated()

    return user


def require_roles(*roles: str):
    """Crea una dependencia que solo deja pasar a los roles indicados."""

    def checker(user: User = Depends(get_current_user)) -> User:
        if user.rol not in roles:
            raise Forbidden()
        return user

    return checker


def get_gestor(user: User = Depends(require_roles("admin", "trabajador"))) -> User:
    """Admin o trabajador. El trabajador además debe tener fundación asignada."""
    if user.rol == "trabajador" and user.fundacion_id is None:
        raise Forbidden("Tu cuenta de trabajador aún no está asociada a una fundación.")
    return user


get_admin = require_roles("admin")

