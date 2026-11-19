from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session
from fastapi.responses import RedirectResponse
from app.services import foto_service
from app.core.flash import flash
from app.core.database import get_db
from app.core.deps import get_optional_user
from app.core.templates import templates
from app.models.user import User
from app.services import catalogo_service
from app.core.config import settings
from app.services import qr_service
from app.services import evento_service
from app.services import ficha_pdf_service
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
def eventos(
    request: Request,
    pasados: bool = False,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_user),
):
    return templates.TemplateResponse(
        request,
        "publico/eventos.html",
        {
            "user": user,
            "eventos": evento_service.listar_publicos(db, pasados),
            "pasados": pasados,
        },
    )


@router.get("/eventos/{evento_id}")
def evento_detalle(
    evento_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_user),
):
    evento = evento_service.obtener_publico(db, evento_id)
    if evento is None:
        flash(request, "Ese evento no existe o ya no está publicado.", "error")
        return RedirectResponse("/eventos", status_code=303)
    return templates.TemplateResponse(
        request, "publico/evento_detalle.html", {"user": user, "evento": evento}
    )


@router.get("/quienes-somos")
def quienes_somos(request: Request, user: User | None = Depends(get_optional_user)):
    return templates.TemplateResponse(request, "publico/quienes_somos.html", {"user": user})

@router.get("/animales/{animal_id}/qr.png")
def qr_imagen(animal_id: int, descargar: bool = False, db: Session = Depends(get_db)):
    animal = catalogo_service.obtener_ficha(db, animal_id)
    if animal is None:
        raise HTTPException(status_code=404)

    # El QR contiene la dirección pública de la app + el token del animal
    enlace = f"{settings.APP_URL.rstrip('/')}/qr/{animal.qr_token}"
    cabeceras = {"Cache-Control": "public, max-age=3600"}
    if descargar:
        cabeceras["Content-Disposition"] = f'attachment; filename="qr-{animal.nombre.lower()}-{animal.id}.png"'
    return Response(qr_service.generar_png(enlace), media_type="image/png", headers=cabeceras)


@router.get("/qr/{token}")
def qr_destino(
    token: str, request: Request, db: Session = Depends(get_db)
):
    """Destino del QR: abre la ficha técnica en PDF del animal."""
    animal = catalogo_service.obtener_por_token(db, token)
    if animal is None:
        flash(request, "Ese código QR no corresponde a ningún animal publicado.", "error")
        return RedirectResponse("/animales", status_code=303)
    return RedirectResponse(f"/animales/{animal.id}/ficha.pdf", status_code=303)

@router.get("/fotos/{foto_id}")
def foto_imagen(foto_id: int, db: Session = Depends(get_db)):
    foto = foto_service.obtener_publica(db, foto_id)
    if foto is None:
        raise HTTPException(status_code=404)
    return Response(
        foto.datos,
        media_type="image/jpeg",
        headers={"Cache-Control": "public, max-age=86400"},
    )

@router.get("/animales/{animal_id}/ficha.pdf")
def ficha_pdf(animal_id: int, descargar: bool = False, db: Session = Depends(get_db)):
    animal = catalogo_service.obtener_ficha_completa(db, animal_id)
    if animal is None:
        raise HTTPException(status_code=404)

    enlace_qr = f"{settings.APP_URL.rstrip('/')}/qr/{animal.qr_token}"
    pdf = ficha_pdf_service.generar(animal, enlace_qr)
    disposicion = "attachment" if descargar else "inline"  # inline: se abre en el navegador o visor del celular
    return Response(
        pdf,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'{disposicion}; filename="ficha-animal-{animal.id}.pdf"',
            "Cache-Control": "no-cache",
        },
    )