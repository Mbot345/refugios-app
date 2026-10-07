from email_validator import EmailNotValidError, validate_email
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password, verify_password
from app.models.user import User


def get_by_username(db: Session, username: str) -> User | None:
    return db.scalar(select(User).where(User.username == username))


def get_by_email(db: Session, email: str) -> User | None:
    return db.scalar(select(User).where(User.email == email))


def validate_registration(
    db: Session, username: str, email: str, password: str, password2: str
) -> list[str]:
    """Devuelve la lista de errores. Si está vacía, los datos son válidos."""
    errors = []

    if not 3 <= len(username) <= 50:
        errors.append("El usuario debe tener entre 3 y 50 caracteres.")
    elif get_by_username(db, username):
        errors.append("Ese nombre de usuario ya está en uso.")

    try:
        validate_email(email, check_deliverability=False)
        if get_by_email(db, email):
            errors.append("Ese correo ya está registrado.")
    except EmailNotValidError:
        errors.append("El correo no es válido.")

    if len(password) < 8:
        errors.append("La contraseña debe tener al menos 8 caracteres.")
    elif len(password.encode("utf-8")) > 72:
        errors.append("La contraseña es demasiado larga (máximo 72 caracteres).")

    if password != password2:
        errors.append("Las contraseñas no coinciden.")

    return errors


def register_user(db: Session, username: str, email: str, password: str) -> User:
    user = User(
        username=username,
        email=email,
        password_hash=hash_password(password),
        rol="adoptante",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate(db: Session, username: str, password: str) -> User | None:
    """Devuelve el usuario si las credenciales son correctas, o None."""
    user = get_by_username(db, username)
    if user is None or not user.activo:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user