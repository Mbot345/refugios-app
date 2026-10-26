from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.core.constants import ROLES
from app.core.database import get_db
from app.core.deps import get_admin
from app.core.flash import flash
from app.core.templates import templates
from app.models.fundacion import Fundacion
from app.models.user import User
from app.services import admin_service, fundacion_service, usuario_service

router = APIRouter(prefix="/admin", dependencies=[Depends(get_admin)])


@router.get("")
def panel(request: Request, db: Session = Depends(get_db), user: User = Depends(get_admin)):
    return templates.TemplateResponse(request, "admin/panel.html", {"user": user, "stats": admin_service.estadisticas(db)})


@router.get("/usuarios")
def usuarios(request: Request, db: Session = Depends(get_db), user: User = Depends(get_admin)):
    return templates.TemplateResponse(request, "admin/usuarios.html", {"user": user, "usuarios": usuario_service.listar(db)})


def _usuario_form(request, db, user, objetivo, datos, status_code=200):
    return templates.TemplateResponse(request, "admin/usuario_form.html", {"user": user, "objetivo": objetivo, "datos": datos, "roles": ROLES, "fundaciones": usuario_service.listar_fundaciones_activas(db)}, status_code=status_code)


@router.get("/usuarios/{usuario_id}/editar")
def usuario_editar_form(usuario_id: int, request: Request, db: Session = Depends(get_db), user: User = Depends(get_admin)):
    objetivo = usuario_service.obtener(db, usuario_id)
    if objetivo is None:
        flash(request, "El usuario no existe.", "error"); return RedirectResponse("/admin/usuarios", status_code=303)
    return _usuario_form(request, db, user, objetivo, {"rol": objetivo.rol, "fundacion_id": str(objetivo.fundacion_id or "")})


@router.post("/usuarios/{usuario_id}/editar")
def usuario_editar(usuario_id: int, request: Request, rol: str = Form(""), fundacion_id: str = Form(""), db: Session = Depends(get_db), user: User = Depends(get_admin)):
    objetivo = usuario_service.obtener(db, usuario_id)
    if objetivo is None:
        flash(request, "El usuario no existe.", "error"); return RedirectResponse("/admin/usuarios", status_code=303)
    errores = usuario_service.validar_cambios(db, user, objetivo, rol, fundacion_id)
    if errores:
        for error in errores: flash(request, error, "error")
        return _usuario_form(request, db, user, objetivo, {"rol": rol, "fundacion_id": fundacion_id}, 400)
    usuario_service.aplicar_cambios(db, objetivo, rol, fundacion_id)
    flash(request, f"Usuario «{objetivo.username}» actualizado.", "success")
    return RedirectResponse("/admin/usuarios", status_code=303)


@router.post("/usuarios/{usuario_id}/estado")
def usuario_estado(usuario_id: int, request: Request, db: Session = Depends(get_db), user: User = Depends(get_admin)):
    objetivo = usuario_service.obtener(db, usuario_id)
    if objetivo is None:
        flash(request, "El usuario no existe.", "error")
    else:
        error = usuario_service.cambiar_estado(db, user, objetivo)
        if error: flash(request, error, "error")
        else: flash(request, f"Usuario «{objetivo.username}» {'activado' if objetivo.activo else 'desactivado'}.", "info")
    return RedirectResponse("/admin/usuarios", status_code=303)


def datos_fundacion(nombre: str = Form(""), descripcion: str = Form(""), direccion: str = Form(""), provincia_id: str = Form(""), ciudad_id: str = Form(""), telefono: str = Form(""), email_contacto: str = Form("")) -> dict:
    return fundacion_service.limpiar_datos(nombre, descripcion, direccion, provincia_id, ciudad_id, telefono, email_contacto)


def _fundacion_form(request, db, user, fundacion=None, datos=None, status_code=200):
    datos = datos or {}; pid = datos.get("provincia_id", "")
    ciudades = fundacion_service.ciudades_de(db, int(pid)) if pid.isdigit() else []
    return templates.TemplateResponse(request, "admin/fundacion_form.html", {"user": user, "fundacion": fundacion, "datos": datos, "provincias": fundacion_service.listar_provincias(db), "ciudades": ciudades}, status_code=status_code)


@router.get("/fundaciones")
def fundaciones(request: Request, db: Session = Depends(get_db), user: User = Depends(get_admin)):
    return templates.TemplateResponse(request, "admin/fundaciones.html", {"user": user, "fundaciones": fundacion_service.listar(db)})


@router.get("/fundaciones/nueva")
def fundacion_nueva(request: Request, db: Session = Depends(get_db), user: User = Depends(get_admin)):
    return _fundacion_form(request, db, user)


@router.post("/fundaciones")
def fundacion_crear(request: Request, datos: dict = Depends(datos_fundacion), db: Session = Depends(get_db), user: User = Depends(get_admin)):
    errores = fundacion_service.validar(db, datos)
    if errores:
        for error in errores: flash(request, error, "error")
        return _fundacion_form(request, db, user, datos=datos, status_code=400)
    f = fundacion_service.crear(db, datos); flash(request, f"Fundación «{f.nombre}» registrada.", "success")
    return RedirectResponse("/admin/fundaciones", status_code=303)


@router.get("/fundaciones/{fundacion_id}/editar")
def fundacion_editar_form(fundacion_id: int, request: Request, db: Session = Depends(get_db), user: User = Depends(get_admin)):
    f = fundacion_service.obtener(db, fundacion_id)
    if f is None:
        flash(request, "La fundación no existe.", "error"); return RedirectResponse("/admin/fundaciones", status_code=303)
    return _fundacion_form(request, db, user, f, fundacion_service.a_datos(f))


@router.post("/fundaciones/{fundacion_id}/editar")
def fundacion_editar(fundacion_id: int, request: Request, datos: dict = Depends(datos_fundacion), db: Session = Depends(get_db), user: User = Depends(get_admin)):
    f = fundacion_service.obtener(db, fundacion_id)
    if f is None:
        flash(request, "La fundación no existe.", "error"); return RedirectResponse("/admin/fundaciones", status_code=303)
    errores = fundacion_service.validar(db, datos, actual_id=f.id)
    if errores:
        for error in errores: flash(request, error, "error")
        return _fundacion_form(request, db, user, f, datos, 400)
    fundacion_service.actualizar(db, f, datos); flash(request, f"Fundación «{f.nombre}» actualizada.", "success")
    return RedirectResponse("/admin/fundaciones", status_code=303)


@router.post("/fundaciones/{fundacion_id}/estado")
def fundacion_estado(fundacion_id: int, request: Request, db: Session = Depends(get_db)):
    f = fundacion_service.obtener(db, fundacion_id)
    if f is None: flash(request, "La fundación no existe.", "error")
    else:
        fundacion_service.cambiar_activa(db, f)
        flash(request, f"Fundación «{f.nombre}» {'activada' if f.activa else 'desactivada'}.", "info")
    return RedirectResponse("/admin/fundaciones", status_code=303)


@router.get("/provincias/{provincia_id}/ciudades")
def ciudades_de_provincia(provincia_id: int, db: Session = Depends(get_db)):
    return [{"id": c.id, "nombre": c.nombre} for c in fundacion_service.ciudades_de(db, provincia_id)]
