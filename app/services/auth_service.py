import re

from email_validator import EmailNotValidError, validate_email
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import hash_password, verify_password
from app.models.ubicacion import Ciudad, Provincia
from app.models.user import User

CODIGOS_PROVINCIA_EC = frozenset(range(1, 25))
TELEFONO_EC = re.compile(r"^(09\d{8}|0[2-7]\d{7})$")


class RegistroDuplicado(Exception):
    """Una restricción única detectó una colisión concurrente durante el registro."""

    def __init__(self, errores: list[str]):
        self.errores = errores
        super().__init__("; ".join(errores))


def normalizar_cedula(valor: str) -> str:
    """Permite espacios y guiones como separadores; devuelve únicamente los dígitos."""
    return re.sub(r"[\s-]", "", valor)


def validar_cedula_ecuatoriana(valor: str) -> bool:
    """Valida estructura y dígito Módulo 10; no comprueba la identidad del titular."""
    cedula = normalizar_cedula(valor)
    if len(cedula) != 10 or not cedula.isdigit():
        return False
    provincia = int(cedula[:2])
    if provincia not in CODIGOS_PROVINCIA_EC or int(cedula[2]) > 5:
        return False

    suma = 0
    for posicion, caracter in enumerate(cedula[:9]):
        digito = int(caracter)
        if posicion % 2 == 0:
            digito *= 2
            if digito > 9:
                digito -= 9
        suma += digito
    verificador = (10 - suma % 10) % 10
    return verificador == int(cedula[9])


def get_by_username(db: Session, username: str) -> User | None:
    return db.scalar(select(User).where(func.lower(User.username) == username.strip().lower()))


def get_by_email(db: Session, email: str) -> User | None:
    return db.scalar(select(User).where(func.lower(User.email) == email.strip().lower()))


def _errores_duplicados(db: Session, datos: dict) -> list[str]:
    errores = []
    if db.scalar(select(User.id).where(func.lower(User.username) == datos["username"])):
        errores.append("Este nombre de usuario ya está registrado.")
    if db.scalar(select(User.id).where(func.lower(User.email) == datos["email"])):
        errores.append("Este correo electrónico ya está registrado.")
    if datos["cedula"] and db.scalar(select(User.id).where(User.cedula == datos["cedula"])):
        errores.append("Esta cédula ya está registrada.")
    return errores


def normalizar_datos_registro(datos: dict) -> dict:
    return {
        **datos,
        "username": datos["username"].strip().lower(),
        "nombres_completos": " ".join(datos["nombres_completos"].split()),
        "email": datos["email"].strip().lower(),
        "cedula": normalizar_cedula(datos["cedula"]),
        "telefono": re.sub(r"[\s()\-]", "", datos["telefono"]),
        "direccion": datos["direccion"].strip(),
        "provincia_id": datos["provincia_id"].strip(),
        "ciudad_id": datos["ciudad_id"].strip(),
    }


def validate_registration(db: Session, datos: dict) -> list[str]:
    datos = normalizar_datos_registro(datos)
    errores = []

    if not 3 <= len(datos["username"]) <= 50:
        errores.append("El usuario debe tener entre 3 y 50 caracteres.")
    if not 3 <= len(datos["nombres_completos"]) <= 150:
        errores.append("Ingresa tus nombres completos (de 3 a 150 caracteres).")

    try:
        validate_email(datos["email"], check_deliverability=False)
    except EmailNotValidError:
        errores.append("El correo electrónico no es válido.")

    password = datos["password"]
    if len(password) < 8:
        errores.append("La contraseña debe tener al menos 8 caracteres.")
    elif len(password.encode("utf-8")) > 72:
        errores.append("La contraseña es demasiado larga (máximo 72 caracteres).")
    if password != datos["password2"]:
        errores.append("Las contraseñas no coinciden.")

    # La comprobación matemática no consulta ni acredita la identidad del titular.
    if not validar_cedula_ecuatoriana(datos["cedula"]):
        errores.append("La cédula ecuatoriana no es válida.")
    if not TELEFONO_EC.fullmatch(datos["telefono"]):
        errores.append("El teléfono debe ser celular (09XXXXXXXX) o convencional (0 + área + 7 dígitos).")
    if not 5 <= len(datos["direccion"]) <= 300:
        errores.append("La dirección debe tener entre 5 y 300 caracteres.")

    provincia = db.get(Provincia, int(datos["provincia_id"])) if datos["provincia_id"].isdigit() else None
    ciudad = db.get(Ciudad, int(datos["ciudad_id"])) if datos["ciudad_id"].isdigit() else None
    if provincia is None:
        errores.append("Selecciona una provincia válida.")
    elif ciudad is None:
        errores.append("Selecciona una ciudad válida.")
    elif ciudad.provincia_id != provincia.id:
        errores.append("La ciudad seleccionada no pertenece a la provincia elegida.")

    errores.extend(_errores_duplicados(db, datos))
    return errores


def register_user(db: Session, datos: dict) -> User:
    datos = normalizar_datos_registro(datos)
    provincia = db.get(Provincia, int(datos["provincia_id"]))
    ciudad = db.get(Ciudad, int(datos["ciudad_id"]))
    user = User(
        username=datos["username"],
        nombres_completos=datos["nombres_completos"],
        email=datos["email"],
        password_hash=hash_password(datos["password"]),
        cedula=datos["cedula"],
        telefono=datos["telefono"],
        provincia=provincia,
        ciudad=ciudad,
        direccion=datos["direccion"],
        # El registro público nunca acepta rol, estado ni fundación desde el cliente.
        rol="adoptante",
        activo=True,
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        duplicados = _errores_duplicados(db, datos)
        if duplicados:
            raise RegistroDuplicado(duplicados) from exc
        raise
    db.refresh(user)
    return user


def authenticate(db: Session, username: str, password: str) -> User | None:
    user = get_by_username(db, username)
    if user is None or not user.activo:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


def ruta_inicial(user: User) -> str:
    """A dónde enviar al usuario después de iniciar sesión, según su rol."""
    if user.rol == "admin":
        return "/admin"
    if user.rol == "trabajador":
        return "/animales"
    return "/"
