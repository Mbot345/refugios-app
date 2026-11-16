from pathlib import Path

from fastapi.templating import Jinja2Templates

from app.core.constants import ROL_ETIQUETAS, ROLES_FUNDACION, ROLES_GLOBALES
from app.core.flash import pop_flashes

BASE_DIR = Path(__file__).resolve().parent.parent

templates = Jinja2Templates(directory=BASE_DIR / "views")
templates.env.globals["get_flashed_messages"] = pop_flashes
templates.env.globals["ROLES_GLOBALES"] = ROLES_GLOBALES
templates.env.globals["ROLES_FUNDACION"] = ROLES_FUNDACION
templates.env.filters["rol_nombre"] = lambda rol: ROL_ETIQUETAS.get(rol, rol)