from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    """Obtiene el usuario guardado en la sesión o redirige al login."""
    user_id = request.session.get("user_id")
    user = db.get(User, user_id) if user_id is not None else None
    if user is None or not user.activo:
        raise HTTPException(
            status_code=303,
            headers={"Location": "/login"},
        )
    return user
