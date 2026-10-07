from pathlib import Path

from fastapi.templating import Jinja2Templates

from app.core.flash import pop_flashes

BASE_DIR = Path(__file__).resolve().parent.parent

templates = Jinja2Templates(directory=BASE_DIR / "views")
templates.env.globals["get_flashed_messages"] = pop_flashes