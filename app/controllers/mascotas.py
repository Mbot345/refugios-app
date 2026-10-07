from pydantic import ValidationError
from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.refugio import Refugio
from app.schemas.mascota import MascotaData
from app.services import mascota_service as service

router = APIRouter(prefix="/mascotas", tags=["mascotas"], dependencies=[Depends(get_current_user)])
templates = Jinja2Templates(directory="app/views")


def _context(request: Request, **extra):
    context = {"request": request, "flash": request.session.pop("flash", None)}
    context.update(extra)
    return context


def _form(request: Request, db: Session, *, valores: dict, errores=None, mascota_id=None, status_code=200):
    refugios = service.obtener_refugios(db)
    return templates.TemplateResponse(
        request=request,
        name="mascotas/form.html",
        context=_context(
            request,
            valores=valores,
            errores=errores or [],
            refugios=refugios,
            mascota_id=mascota_id,
        ),
        status_code=status_code,
    )


def _form_values(mascota=None) -> dict:
    if mascota is None:
        return {"nombre": "", "especie": "", "raza": "", "sexo": "", "fecha_nacimiento": "", "descripcion": "", "estado": "disponible", "refugio_id": ""}
    return {
        "nombre": mascota.nombre,
        "especie": mascota.especie,
        "raza": mascota.raza or "",
        "sexo": mascota.sexo,
        "fecha_nacimiento": mascota.fecha_nacimiento.isoformat() if mascota.fecha_nacimiento else "",
        "descripcion": mascota.descripcion or "",
        "estado": mascota.estado,
        "refugio_id": str(mascota.refugio_id),
    }


def _form_errors(error: ValidationError) -> list[str]:
    labels = {
        "nombre": "Nombre", "especie": "Especie", "raza": "Raza", "sexo": "Sexo",
        "fecha_nacimiento": "Fecha de nacimiento", "descripcion": "Descripción",
        "estado": "Estado", "refugio_id": "Refugio",
    }
    return [f"{labels.get(str(e['loc'][0]), 'Dato')}: {e['msg']}" for e in error.errors()]


@router.get("")
def listar_mascotas(request: Request, db: Session = Depends(get_db)):
    return templates.TemplateResponse(
        request=request,
        name="mascotas/lista.html",
        context=_context(request, mascotas=service.obtener_mascotas(db)),
    )


@router.get("/nueva")
def nueva_mascota(request: Request, db: Session = Depends(get_db)):
    return _form(request, db, valores=_form_values())


@router.post("/nueva")
def crear_mascota(
    request: Request,
    nombre: str = Form(""), especie: str = Form(""), raza: str = Form(""),
    sexo: str = Form(""), fecha_nacimiento: str = Form(""), descripcion: str = Form(""),
    estado: str = Form(""), refugio_id: str = Form(""), db: Session = Depends(get_db),
):
    valores = {"nombre": nombre, "especie": especie, "raza": raza, "sexo": sexo,
               "fecha_nacimiento": fecha_nacimiento, "descripcion": descripcion,
               "estado": estado, "refugio_id": refugio_id}
    try:
        datos = MascotaData.model_validate(valores)
    except ValidationError as error:
        return _form(request, db, valores=valores, errores=_form_errors(error), status_code=422)
    if db.get(Refugio, datos.refugio_id) is None:
        return _form(request, db, valores=valores, errores=["Selecciona un refugio existente."], status_code=422)
    service.crear_mascota(db, datos)
    request.session["flash"] = "Mascota creada correctamente."
    return RedirectResponse("/mascotas", status_code=303)


@router.get("/{mascota_id}")
def detalle_mascota(mascota_id: int, request: Request, db: Session = Depends(get_db)):
    mascota = service.obtener_mascota(db, mascota_id)
    if mascota is None:
        request.session["flash"] = "Mascota no encontrada."
        return RedirectResponse("/mascotas", status_code=303)
    return templates.TemplateResponse(
        request=request,
        name="mascotas/detalle.html",
        context=_context(request, mascota=mascota),
    )


@router.get("/{mascota_id}/editar")
def editar_formulario(mascota_id: int, request: Request, db: Session = Depends(get_db)):
    mascota = service.obtener_mascota(db, mascota_id)
    if mascota is None:
        request.session["flash"] = "Mascota no encontrada."
        return RedirectResponse("/mascotas", status_code=303)
    return _form(request, db, valores=_form_values(mascota), mascota_id=mascota.id)


@router.post("/{mascota_id}/editar")
def actualizar_mascota(
    mascota_id: int, request: Request,
    nombre: str = Form(""), especie: str = Form(""), raza: str = Form(""),
    sexo: str = Form(""), fecha_nacimiento: str = Form(""), descripcion: str = Form(""),
    estado: str = Form(""), refugio_id: str = Form(""), db: Session = Depends(get_db),
):
    mascota = service.obtener_mascota(db, mascota_id)
    if mascota is None:
        request.session["flash"] = "Mascota no encontrada."
        return RedirectResponse("/mascotas", status_code=303)
    valores = {"nombre": nombre, "especie": especie, "raza": raza, "sexo": sexo,
               "fecha_nacimiento": fecha_nacimiento, "descripcion": descripcion,
               "estado": estado, "refugio_id": refugio_id}
    try:
        datos = MascotaData.model_validate(valores)
    except ValidationError as error:
        return _form(request, db, valores=valores, errores=_form_errors(error), mascota_id=mascota_id, status_code=422)
    if db.get(Refugio, datos.refugio_id) is None:
        return _form(request, db, valores=valores, errores=["Selecciona un refugio existente."], mascota_id=mascota_id, status_code=422)
    service.actualizar_mascota(db, mascota, datos)
    request.session["flash"] = "Mascota actualizada correctamente."
    return RedirectResponse(f"/mascotas/{mascota_id}", status_code=303)


@router.post("/{mascota_id}/eliminar")
def eliminar_mascota(mascota_id: int, request: Request, db: Session = Depends(get_db)):
    mascota = service.obtener_mascota(db, mascota_id)
    if mascota is None:
        request.session["flash"] = "Mascota no encontrada."
    else:
        service.eliminar_mascota(db, mascota)
        request.session["flash"] = "Mascota eliminada correctamente."
    return RedirectResponse("/mascotas", status_code=303)
