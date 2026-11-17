import re
from datetime import date, datetime

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, contains_eager, joinedload

from app.core.constants import TENENCIAS_VIVIENDA, TIPOS_VIVIENDA
from app.core.validators import TELEFONO_CONVENCIONAL, TELEFONO_MOVIL, cedula_valida
from app.models.animal import Animal
from app.models.fundacion import Fundacion
from app.models.solicitud import HistorialSolicitud, SolicitudPreadopcion
from app.models.user import User


def obtener_solicitable(db: Session, animal_id: int) -> Animal | None:
    """Solo se puede solicitar un animal disponible de una fundación activa."""
    consulta = (
        select(Animal)
        .join(Animal.fundacion)
        .options(contains_eager(Animal.fundacion))
        .where(
            Animal.id == animal_id,
            Animal.estado == "disponible",
            Fundacion.activa.is_(True),
        )
    )
    return db.scalar(consulta)


def tiene_pendiente(db: Session, animal_id: int, usuario_id: int) -> bool:
    consulta = select(SolicitudPreadopcion.id).where(
        SolicitudPreadopcion.animal_id == animal_id,
        SolicitudPreadopcion.usuario_id == usuario_id,
        SolicitudPreadopcion.estado == "pendiente",
    )
    return db.scalar(consulta) is not None


def listar_de_usuario(db: Session, user: User) -> list[SolicitudPreadopcion]:
    consulta = (
        select(SolicitudPreadopcion)
        .options(joinedload(SolicitudPreadopcion.animal).joinedload(Animal.fundacion))
        .where(SolicitudPreadopcion.usuario_id == user.id)
        .order_by(SolicitudPreadopcion.fecha_solicitud.desc())
    )
    return list(db.scalars(consulta).all())


def limpiar_datos(
    nombres_completos: str,
    cedula: str,
    fecha_nacimiento: str,
    telefono_convencional: str,
    telefono_movil: str,
    direccion_vivienda: str,
    ocupacion: str,
    tipo_vivienda: str,
    metros_vivienda: str,
    metros_area_verde: str,
    dimension_area_comunal: str,
    tenencia_vivienda: str,
    motivo_adopcion: str,
    acepta_visitas: str,
    experiencia_previa: str,
) -> dict:
    """Normaliza: sin espacios sobrantes, teléfonos solo con dígitos, vacíos opcionales en None."""
    quitar = r"[\s\-]"
    return {
        "nombres_completos": " ".join(nombres_completos.split()),
        "cedula": cedula.strip(),
        "fecha_nacimiento": fecha_nacimiento.strip(),
        "telefono_convencional": re.sub(quitar, "", telefono_convencional) or None,
        "telefono_movil": re.sub(quitar, "", telefono_movil),
        "direccion_vivienda": direccion_vivienda.strip(),
        "ocupacion": ocupacion.strip(),
        "tipo_vivienda": tipo_vivienda,
        "metros_vivienda": metros_vivienda.strip(),
        "metros_area_verde": metros_area_verde.strip(),
        "dimension_area_comunal": dimension_area_comunal.strip() or None,
        "tenencia_vivienda": tenencia_vivienda,
        "motivo_adopcion": motivo_adopcion.strip(),
        "acepta_visitas": acepta_visitas,
        "experiencia_previa": experiencia_previa.strip() or None,
    }


def parsear_fecha(texto: str) -> date | None:
    """Acepta aaaa-mm-dd (campo de fecha del navegador) y dd/mm/aaaa."""
    for formato in ("%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(texto, formato).date()
        except ValueError:
            continue
    return None


def _edad(nacimiento: date, hoy: date) -> int:
    return hoy.year - nacimiento.year - ((hoy.month, hoy.day) < (nacimiento.month, nacimiento.day))


def _entero(texto: str, minimo: int, maximo: int) -> int | None:
    if re.fullmatch(r"[0-9]+", texto) and minimo <= int(texto) <= maximo:
        return int(texto)
    return None


def validar(datos: dict) -> list[str]:
    """Validación en el servidor. Devuelve la lista de errores (vacía si todo es válido)."""
    errores = []

    nombres = datos["nombres_completos"]
    if not 5 <= len(nombres) <= 120 or len(nombres.split()) < 2:
        errores.append("Escribe tus nombres y apellidos completos.")

    # Dato sensible: se valida con el algoritmo oficial antes de grabarlo
    if not cedula_valida(datos["cedula"]):
        errores.append("La cédula de ciudadanía no es válida.")

    nacimiento = parsear_fecha(datos["fecha_nacimiento"])
    if nacimiento is None:
        errores.append("La fecha de nacimiento no es válida (dd/mm/aaaa).")
    else:
        edad = _edad(nacimiento, date.today())
        if edad < 18:
            errores.append("Debes ser mayor de edad para solicitar una adopción.")
        elif edad > 100:
            errores.append("La fecha de nacimiento no es válida.")

    if not TELEFONO_MOVIL.match(datos["telefono_movil"]):
        errores.append("El teléfono móvil no es válido: debe ser 09 seguido de 8 dígitos.")
    if datos["telefono_convencional"] and not TELEFONO_CONVENCIONAL.match(
        datos["telefono_convencional"]
    ):
        errores.append(
            "El teléfono convencional no es válido: código de área (02 a 07) y 7 dígitos."
        )

    if not 10 <= len(datos["direccion_vivienda"]) <= 200:
        errores.append("La dirección de la vivienda debe tener entre 10 y 200 caracteres.")
    if not 3 <= len(datos["ocupacion"]) <= 100:
        errores.append("La ocupación o profesión debe tener entre 3 y 100 caracteres.")

    if datos["tipo_vivienda"] not in TIPOS_VIVIENDA:
        errores.append("Selecciona un tipo de vivienda válido.")
    if _entero(datos["metros_vivienda"], 1, 100000) is None:
        errores.append("Los metros cuadrados de la vivienda deben ser un número mayor a 0.")
    if _entero(datos["metros_area_verde"], 0, 100000) is None:
        errores.append("Los metros de área verde deben ser un número (0 si no tiene).")
    if datos["dimension_area_comunal"] and len(datos["dimension_area_comunal"]) > 100:
        errores.append("La dimensión del área comunal no puede superar los 100 caracteres.")
    if datos["tenencia_vivienda"] not in TENENCIAS_VIVIENDA:
        errores.append("Indica si la vivienda es propia, arrendada o prestada.")

    if not 20 <= len(datos["motivo_adopcion"]) <= 1000:
        errores.append("Explica tus motivos para adoptar (entre 20 y 1000 caracteres).")
    if datos["acepta_visitas"] not in ("si", "no"):
        errores.append("Indica si aceptas las visitas de seguimiento.")
    if datos["experiencia_previa"] and len(datos["experiencia_previa"]) > 1000:
        errores.append("La experiencia previa no puede superar los 1000 caracteres.")

    return errores


def crear(
    db: Session, user: User, animal: Animal, datos: dict
) -> SolicitudPreadopcion | None:
    """Guarda la solicitud (estado pendiente) con su primer registro en el historial."""
    solicitud = SolicitudPreadopcion(
        estado="pendiente",
        animal_id=animal.id,
        usuario_id=user.id,
        nombres_completos=datos["nombres_completos"],
        cedula=datos["cedula"],
        fecha_nacimiento=parsear_fecha(datos["fecha_nacimiento"]),
        telefono_convencional=datos["telefono_convencional"],
        telefono_movil=datos["telefono_movil"],
        direccion_vivienda=datos["direccion_vivienda"],
        ocupacion=datos["ocupacion"],
        tipo_vivienda=datos["tipo_vivienda"],
        metros_vivienda=int(datos["metros_vivienda"]),
        metros_area_verde=int(datos["metros_area_verde"]),
        dimension_area_comunal=datos["dimension_area_comunal"],
        tenencia_vivienda=datos["tenencia_vivienda"],
        motivo_adopcion=datos["motivo_adopcion"],
        acepta_visitas=datos["acepta_visitas"] == "si",
        experiencia_previa=datos["experiencia_previa"],
    )
    solicitud.historial.append(
        HistorialSolicitud(
            estado_anterior=None,
            estado_nuevo="pendiente",
            observacion="Solicitud enviada",
            usuario_id=user.id,
        )
    )
    db.add(solicitud)
    try:
        db.commit()
    except IntegrityError:
        # Última barrera: el índice único de la base impide la solicitud pendiente duplicada
        db.rollback()
        return None
    db.refresh(solicitud)
    return solicitud