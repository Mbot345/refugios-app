from pathlib import Path

from fastapi.templating import Jinja2Templates

from app.core.constants import ROL_ETIQUETAS, ROLES_FUNDACION, ROLES_GLOBALES
from app.core.flash import pop_flashes
from app.core.fechas import a_hora_local
from app.services import linea_tiempo

BASE_DIR = Path(__file__).resolve().parent.parent


def formato_edad(meses: int | None) -> str:
    """Convierte meses en texto legible: '8 meses', '2 años', '2 años y 3 meses'."""
    if meses is None:
        return "Edad no registrada"
    anios, resto = divmod(meses, 12)
    partes = []
    if anios:
        partes.append(f"{anios} año" + ("s" if anios != 1 else ""))
    if resto or not anios:
        partes.append(f"{resto} mes" + ("es" if resto != 1 else ""))
    return " y ".join(partes)


templates = Jinja2Templates(directory=BASE_DIR / "views")
templates.env.globals["get_flashed_messages"] = pop_flashes
templates.env.globals["ROLES_GLOBALES"] = ROLES_GLOBALES
templates.env.globals["ROLES_FUNDACION"] = ROLES_FUNDACION
templates.env.filters["rol_nombre"] = lambda rol: ROL_ETIQUETAS.get(rol, rol)
templates.env.filters["edad"] = formato_edad
templates.env.globals["linea_tiempo"] = linea_tiempo.construir
templates.env.filters["hora_ec"] = a_hora_local