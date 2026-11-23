from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_optional_user
from app.core.templates import templates
from app.models.user import User
from app.services import catalogo_service, evento_service

router = APIRouter()


@router.get("/")
def home(
    request: Request,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_user),
):
    # Solo lectura: los últimos animales publicados y las próximas campañas
    animales = catalogo_service.listar_disponibles(db)[:4]
    eventos = [e for e in evento_service.listar_publicos(db) if e.estado != "cancelado"][:3]
    return templates.TemplateResponse(
        request,
        "home.html",
        {"user": user, "animales": animales, "eventos": eventos},
    )
