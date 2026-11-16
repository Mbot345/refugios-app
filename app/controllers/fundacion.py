from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.core.constants import ROLES_FUNDACION
from app.core.database import get_db
from app.core.deps import get_admin_fundacion, get_miembro_fundacion
from app.core.flash import flash
from app.core.templates import templates
from app.models.user import User
from app.services import equipo_service, fundacion_service

# Cualquier rol de fundación entra; cada ruta restringe más cuando hace falta
router = APIRouter(prefix="/fundacion", dependencies=[Depends(get_miembro_fundacion)])


@router.get("")
def panel(request: Request, user: User = Depends(get_miembro_fundacion)):
    return templates.TemplateResponse(
        request, "fundacion/panel.html", {"user": user, "fundacion": user.fundacion}
    )


# ---------- Perfil de la fundación ----------
def _render_perfil(request: Request, user: User, datos: dict, status_code: int = 200):
    return templates.TemplateResponse(
        request,
        "fundacion/perfil.html",
        {"user": user, "fundacion": user.fundacion, "datos": datos},
        status_code=status_code,
    )


@router.get("/perfil")
def perfil_form(request: Request, user: User = Depends(get_admin_fundacion)):
    return _render_perfil(request, user, fundacion_service.a_datos_perfil(user.fundacion))


@router.post("/perfil")
def perfil_guardar(
    request: Request,
    descripcion: str = Form(""),
    direccion: str = Form(""),
    telefono: str = Form(""),
    email_contacto: str = Form(""),
    db: Session = Depends(get_db),
    user: User = Depends(get_admin_fundacion),
):
    datos = fundacion_service.limpiar_perfil(descripcion, direccion, telefono, email_contacto)
    errores = fundacion_service.validar_perfil(datos)
    if errores:
        for error in errores:
            flash(request, error, "error")
        return _render_perfil(request, user, datos, status_code=400)

    fundacion_service.actualizar_perfil(db, user.fundacion, datos)
    flash(request, "Perfil de la fundación actualizado.", "success")
    return RedirectResponse("/fundacion", status_code=303)


# ---------- Equipo ----------
def _render_equipo(
    request: Request,
    db: Session,
    user: User,
    datos: dict | None = None,
    status_code: int = 200,
):
    return templates.TemplateResponse(
        request,
        "fundacion/equipo.html",
        {
            "user": user,
            "fundacion": user.fundacion,
            "equipo": equipo_service.listar_equipo(db, user.fundacion_id),
            "roles": ROLES_FUNDACION,
            "datos": datos or {},
        },
        status_code=status_code,
    )


@router.get("/equipo")
def equipo(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_admin_fundacion),
):
    return _render_equipo(request, db, user)


@router.post("/equipo/agregar")
def equipo_agregar(
    request: Request,
    identificador: str = Form(""),
    rol: str = Form(""),
    db: Session = Depends(get_db),
    user: User = Depends(get_admin_fundacion),
):
    candidato, errores = equipo_service.validar_alta(db, identificador, rol)
    if errores:
        for error in errores:
            flash(request, error, "error")
        return _render_equipo(
            request, db, user, datos={"identificador": identificador, "rol": rol}, status_code=400
        )

    equipo_service.asignar(db, candidato, rol, user.fundacion_id)
    flash(request, f"«{candidato.username}» se sumó al equipo.", "success")
    return RedirectResponse("/fundacion/equipo", status_code=303)


@router.post("/equipo/{usuario_id}/rol")
def equipo_cambiar_rol(
    usuario_id: int,
    request: Request,
    rol: str = Form(""),
    db: Session = Depends(get_db),
    user: User = Depends(get_admin_fundacion),
):
    miembro = equipo_service.obtener_miembro(db, user.fundacion_id, usuario_id)
    if miembro is None:
        flash(request, "Ese usuario no pertenece a tu equipo.", "error")
        return RedirectResponse("/fundacion/equipo", status_code=303)

    errores = equipo_service.validar_cambio(user, miembro, rol)
    if errores:
        for error in errores:
            flash(request, error, "error")
        return RedirectResponse("/fundacion/equipo", status_code=303)

    equipo_service.cambiar_rol(db, miembro, rol)
    flash(request, f"Rol de «{miembro.username}» actualizado.", "success")
    return RedirectResponse("/fundacion/equipo", status_code=303)


@router.post("/equipo/{usuario_id}/quitar")
def equipo_quitar(
    usuario_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_admin_fundacion),
):
    miembro = equipo_service.obtener_miembro(db, user.fundacion_id, usuario_id)
    if miembro is None:
        flash(request, "Ese usuario no pertenece a tu equipo.", "error")
        return RedirectResponse("/fundacion/equipo", status_code=303)

    error = equipo_service.validar_quitar(user, miembro)
    if error:
        flash(request, error, "error")
        return RedirectResponse("/fundacion/equipo", status_code=303)

    equipo_service.quitar(db, miembro)
    flash(request, f"«{miembro.username}» salió del equipo.", "info")
    return RedirectResponse("/fundacion/equipo", status_code=303)