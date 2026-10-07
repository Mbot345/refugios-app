from fastapi import Depends, FastAPI, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import text
from sqlalchemy.orm import Session
from starlette.middleware.sessions import SessionMiddleware

from app.controllers import auth, home, mascotas
from app.core.config import settings
from app.core.database import get_db
from app.core.deps import NotAuthenticated
from pathlib import Path
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="Refugios App")
BASE_DIR = Path(__file__).resolve().parent
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")

# Sesión en cookie firmada con la SECRET_KEY (dura 8 horas)
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SECRET_KEY,
    max_age=60 * 60 * 8,
    same_site="lax",
)


@app.exception_handler(NotAuthenticated)
async def not_authenticated_handler(request: Request, exc: NotAuthenticated):
    """Sin sesión válida, se redirige siempre al login."""
    return RedirectResponse("/login", status_code=303)


app.include_router(home.router)
app.include_router(auth.router)
app.include_router(mascotas.router)


@app.get("/health")
def health(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    return {"status": "ok", "database": "conectada"}