from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_eventos, get_panel
from app.core.flash import flash
from app.core.templates import templates
from app.models.evento import Evento
from app.models.user import User
from app.services import evento_service as service

# Personal de la fundación: administrador de fundación y encargado de eventos
router = APIRouter(prefix="/fundacion/eventos", dependencies=[Depends(get_eventos)])

# Supervisión de solo lectura para administrador general y moderador
supervision = APIRouter(prefix="/admin/eventos", dependencies=[Depends(get_panel)])


def datos_formulario(
    titulo: str = Form(""),
    descripcion: str = Form(""),
    fecha: str = Form(""),
    hora: str = Form(""),
    lugar: str = Form(""),
) -> dict:
    return service.limpiar_datos(titulo, descripcion, fecha, hora, lugar)


def _render_form(
    request: Request,
    user: User,
    evento: Evento | None = None,
    datos: dict | None = None,
    status_code: int = 200,
):
    return templates.TemplateResponse(
        request,
        "fundacion/evento_form.html",
        {"user": user, "evento": evento, "datos": datos or {}},
        status_code=status_code,
    )


def _no_existe(request: Request):
    flash(request, "El evento no existe o no pertenece a tu fundación.", "error")
    return RedirectResponse("/fundacion/eventos", status_code=303)


@router.get("")
def lista(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_eventos),
):
    return templates.TemplateResponse(
        request,
        "fundacion/eventos_lista.html",
        {"user": user, "eventos": service.listar_de_fundacion(db, user.fundacion_id)},
    )


@router.get("/nuevo")
def nuevo(request: Request, user: User = Depends(get_eventos)):
    return _render_form(request, user)


@router.post("")
def crear(
    request: Request,
    datos: dict = Depends(datos_formulario),
    db: Session = Depends(get_db),
    user: User = Depends(get_eventos),
):
    errores = service.validar(user, datos)
    if errores:
        for error in errores:
            flash(request, error, "error")
        return _render_form(request, user, datos=datos, status_code=400)

    evento = service.crear(db, user, datos)
    flash(request, f"Evento «{evento.titulo}» creado.", "success")
    return RedirectResponse("/fundacion/eventos", status_code=303)


@router.get("/{evento_id}/editar")
def editar_form(
    evento_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_eventos),
):
    evento = service.obtener_de_fundacion(db, evento_id, user.fundacion_id)
    if evento is None:
        return _no_existe(request)

    motivo = service.motivo_no_editable(evento)
    if motivo:
        flash(request, motivo, "error")
        return RedirectResponse("/fundacion/eventos", status_code=303)
    return _render_form(request, user, evento=evento, datos=service.a_datos(evento))


@router.post("/{evento_id}/editar")
def editar(
    evento_id: int,
    request: Request,
    datos: dict = Depends(datos_formulario),
    db: Session = Depends(get_db),
    user: User = Depends(get_eventos),
):
    evento = service.obtener_de_fundacion(db, evento_id, user.fundacion_id)
    if evento is None:
        return _no_existe(request)

    motivo = service.motivo_no_editable(evento)
    if motivo:
        flash(request, motivo, "error")
        return RedirectResponse("/fundacion/eventos", status_code=303)

    errores = service.validar(user, datos)
    if errores:
        for error in errores:
            flash(request, error, "error")
        return _render_form(request, user, evento=evento, datos=datos, status_code=400)

    service.actualizar(db, evento, datos)
    flash(request, f"Evento «{evento.titulo}» actualizado.", "success")
    return RedirectResponse("/fundacion/eventos", status_code=303)


@router.post("/{evento_id}/cancelar")
def cancelar(
    evento_id: int,
    request: Request,
    motivo: str = Form(""),
    db: Session = Depends(get_db),
    user: User = Depends(get_eventos),
):
    evento = service.obtener_de_fundacion(db, evento_id, user.fundacion_id)
    if evento is None:
        return _no_existe(request)

    errores = service.cancelar(db, user, evento, motivo)
    if errores:
        for error in errores:
            flash(request, error, "error")
    else:
        flash(request, f"Evento «{evento.titulo}» cancelado.", "success")
    return RedirectResponse("/fundacion/eventos", status_code=303)


@supervision.get("")
def supervisar(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_panel),
):
    return templates.TemplateResponse(
        request,
        "admin/eventos.html",
        {"user": user, "eventos": service.listar_todos(db)},
    )