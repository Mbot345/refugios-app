from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from fastapi.responses import RedirectResponse

from app.core.flash import flash
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
    especie: str = "",
    tamano: str = "",
    sexo: str = "",
    raza: str = "",
    edad: str = "",
    db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_user),
):
    filtros = {
        "especie": especie.strip(),
        "tamano": tamano.strip(),
        "sexo": sexo.strip(),
        "raza": raza.strip()[:80],
        "edad": edad.strip(),
    }
    return templates.TemplateResponse(
        request,
        "publico/animales.html",
        {
            "user": user,
            "animales": catalogo_service.listar_disponibles(db, filtros),
            "filtros": filtros,
            "opciones": catalogo_service.opciones_filtro(db),
            "rangos_edad": catalogo_service.RANGOS_EDAD,
        },
    )


@router.get("/animales/{animal_id}")
def ficha_animal(
    animal_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_user),
):
    animal = catalogo_service.obtener_ficha(db, animal_id)
    if animal is None:
        flash(request, "Ese animal no existe o ya no está publicado.", "error")
        return RedirectResponse("/animales", status_code=303)
    return templates.TemplateResponse(
        request, "publico/animal_ficha.html", {"user": user, "animal": animal}
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