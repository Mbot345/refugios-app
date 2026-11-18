from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.core.constants import TIPOS_REGISTRO_SANITARIO
from app.models.animal import Animal, RegistroSanitario
from app.models.user import User


def limpiar(tipo: str, descripcion: str, fecha: str) -> dict:
    return {
        "tipo": tipo,
        "descripcion": " ".join(descripcion.split()),
        "fecha": fecha.strip(),
    }


def _parsear_fecha(texto: str) -> date | None:
    try:
        return date.fromisoformat(texto)  # el campo de fecha del navegador envía aaaa-mm-dd
    except ValueError:
        return None


def validar(user: User, datos: dict) -> list[str]:
    errores = []

    if not user.fundacion.activa:
        errores.append("Tu fundación está suspendida: solo puedes consultar la información.")

    if datos["tipo"] not in TIPOS_REGISTRO_SANITARIO:
        errores.append("Selecciona un tipo de registro válido.")
    if not 3 <= len(datos["descripcion"]) <= 300:
        errores.append("La descripción debe tener entre 3 y 300 caracteres.")

    fecha = _parsear_fecha(datos["fecha"])
    hoy = date.today()
    if fecha is None:
        errores.append("La fecha no es válida.")
    elif fecha > hoy:
        errores.append("La fecha del registro no puede ser futura.")
    elif fecha < hoy - timedelta(days=365 * 30):
        errores.append("La fecha del registro es demasiado antigua.")

    return errores


def agregar(db: Session, animal: Animal, datos: dict) -> RegistroSanitario:
    registro = RegistroSanitario(
        tipo=datos["tipo"],
        descripcion=datos["descripcion"],
        fecha=_parsear_fecha(datos["fecha"]),
        animal_id=animal.id,
    )
    db.add(registro)
    db.commit()
    return registro


def eliminar(db: Session, animal: Animal, registro_id: int) -> bool:
    """Elimina el registro solo si pertenece a ese animal."""
    registro = db.get(RegistroSanitario, registro_id)
    if registro is None or registro.animal_id != animal.id:
        return False
    db.delete(registro)
    db.commit()
    return True