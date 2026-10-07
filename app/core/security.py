import bcrypt


def hash_password(password: str) -> str:
    """Convierte la contraseña en un hash irreversible."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    """Compara la contraseña escrita con el hash guardado."""
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))