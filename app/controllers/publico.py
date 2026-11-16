from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_optional_user
from app.core.templates import templates
from app.models.user import User
from app.services import catalogo_service

# Páginas públicas: no exigen sesión, pero si la hay, el menú muestra al usuario
router = APIRouter()


@router.get("/animales")
def catalogo(
    request: Request,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_user),
):
    return templates.TemplateResponse(
        request,
        "publico/animales.html",
        {"user": user, "animales": catalogo_service.listar_disponibles(db)},
    )


@router.get("/fundaciones")
def fundaciones(
    request: Request,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_user),
):
    return templates.TemplateResponse(
        request,
        "publico/fundaciones.html",
        {
            "user": user,
            "fundaciones": catalogo_service.listar_fundaciones_activas(db),
            "disponibles": catalogo_service.conteo_disponibles(db),
        },
    )


@router.get("/eventos")
def eventos(request: Request, user: User | None = Depends(get_optional_user)):
    return templates.TemplateResponse(request, "publico/eventos.html", {"user": user})


@router.get("/quienes-somos")
def quienes_somos(request: Request, user: User | None = Depends(get_optional_user)):
    return templates.TemplateResponse(request, "publico/quienes_somos.html", {"user": user})