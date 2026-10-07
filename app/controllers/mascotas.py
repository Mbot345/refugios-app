from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.flash import flash
from app.core.templates import templates
from app.models.mascota import Mascota
from app.models.user import User
from app.services import mascota_service as service

router = APIRouter(prefix="/mascotas", dependencies=[Depends(get_current_user)])


def _render_form(request: Request, db: Session, user: User,
                 mascota: Mascota | None = None, datos: dict | None = None,
                 status_code: int = 200):
    return templates.TemplateResponse(
        request, "mascotas/form.html",
        {"user": user, "mascota": mascota, "datos": datos or {},
         "refugios": service.listar_refugios(db), "especies": service.ESPECIES,
         "sexos": service.SEXOS, "estados": service.ESTADOS},
        status_code=status_code,
    )


def _no_existe(request: Request):
    flash(request, "La mascota no existe.", "error")
    return RedirectResponse("/mascotas", status_code=303)


@router.get("")
def lista(request: Request, db: Session = Depends(get_db),
          user: User = Depends(get_current_user)):
    return templates.TemplateResponse(
        request, "mascotas/lista.html", {"user": user, "mascotas": service.listar(db)}
    )


@router.get("/nueva")
def nueva(request: Request, db: Session = Depends(get_db),
          user: User = Depends(get_current_user)):
    return _render_form(request, db, user, datos={"estado": "disponible"})


@router.post("")
def crear(request: Request, nombre: str = Form(""), especie: str = Form(""),
          raza: str = Form(""), sexo: str = Form(""), fecha_nacimiento: str = Form(""),
          descripcion: str = Form(""), estado: str = Form("disponible"),
          refugio_id: str = Form(""), db: Session = Depends(get_db),
          user: User = Depends(get_current_user)):
    datos = service.limpiar_datos(nombre, especie, raza, sexo, fecha_nacimiento,
                                  descripcion, estado, refugio_id)
    errores = service.validar(db, datos)
    if errores:
        for error in errores:
            flash(request, error, "error")
        return _render_form(request, db, user, datos=datos, status_code=400)
    mascota = service.crear(db, datos)
    flash(request, f"Mascota «{mascota.nombre}» creada.", "success")
    return RedirectResponse("/mascotas", status_code=303)


@router.get("/{mascota_id}/editar")
def editar_form(mascota_id: int, request: Request, db: Session = Depends(get_db),
                user: User = Depends(get_current_user)):
    mascota = service.obtener(db, mascota_id)
    if mascota is None:
        return _no_existe(request)
    return _render_form(request, db, user, mascota=mascota, datos=service.a_datos(mascota))


@router.post("/{mascota_id}/editar")
def editar(mascota_id: int, request: Request, nombre: str = Form(""), especie: str = Form(""),
           raza: str = Form(""), sexo: str = Form(""), fecha_nacimiento: str = Form(""),
           descripcion: str = Form(""), estado: str = Form("disponible"),
           refugio_id: str = Form(""), db: Session = Depends(get_db),
           user: User = Depends(get_current_user)):
    mascota = service.obtener(db, mascota_id)
    if mascota is None:
        return _no_existe(request)
    datos = service.limpiar_datos(nombre, especie, raza, sexo, fecha_nacimiento,
                                  descripcion, estado, refugio_id)
    errores = service.validar(db, datos)
    if errores:
        for error in errores:
            flash(request, error, "error")
        return _render_form(request, db, user, mascota=mascota, datos=datos, status_code=400)
    service.actualizar(db, mascota, datos)
    flash(request, f"Mascota «{mascota.nombre}» actualizada.", "success")
    return RedirectResponse("/mascotas", status_code=303)


@router.post("/{mascota_id}/eliminar")
def eliminar(mascota_id: int, request: Request, db: Session = Depends(get_db)):
    mascota = service.obtener(db, mascota_id)
    if mascota is None:
        return _no_existe(request)
    nombre = mascota.nombre
    service.eliminar(db, mascota)
    flash(request, f"Mascota «{nombre}» eliminada.", "info")
    return RedirectResponse("/mascotas", status_code=303)
