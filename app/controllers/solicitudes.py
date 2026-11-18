from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from app.services import correo_service
from app.core.constants import ESTADOS_SOLICITUD, TENENCIAS_VIVIENDA, TIPOS_VIVIENDA
from app.core.database import get_db
from app.core.deps import get_adoptante
from app.core.flash import flash
from app.core.templates import templates
from app.models.animal import Animal
from app.models.user import User
from app.services import solicitud_service as service
from app.services.revision_service import ReglaNegocio, cancelar_propia

# Solo el rol adoptante. Sin sesión redirige a /login; con otro rol, muestra el aviso de permiso.
router = APIRouter(dependencies=[Depends(get_adoptante)])


def datos_formulario(
    nombres_completos: str = Form(""),
    cedula: str = Form(""),
    fecha_nacimiento: str = Form(""),
    telefono_convencional: str = Form(""),
    telefono_movil: str = Form(""),
    direccion_vivienda: str = Form(""),
    ocupacion: str = Form(""),
    tipo_vivienda: str = Form(""),
    metros_vivienda: str = Form(""),
    metros_area_verde: str = Form(""),
    dimension_area_comunal: str = Form(""),
    tenencia_vivienda: str = Form(""),
    motivo_adopcion: str = Form(""),
    acepta_visitas: str = Form(""),
    experiencia_previa: str = Form(""),
) -> dict:
    return service.limpiar_datos(
        nombres_completos, cedula, fecha_nacimiento, telefono_convencional, telefono_movil,
        direccion_vivienda, ocupacion, tipo_vivienda, metros_vivienda, metros_area_verde,
        dimension_area_comunal, tenencia_vivienda, motivo_adopcion, acepta_visitas,
        experiencia_previa,
    )


def _render_form(
    request: Request, user: User, animal: Animal, datos: dict, status_code: int = 200
):
    return templates.TemplateResponse(
        request,
        "solicitudes/form.html",
        {
            "user": user,
            "animal": animal,
            "datos": datos,
            "tipos_vivienda": TIPOS_VIVIENDA,
            "tenencias": TENENCIAS_VIVIENDA,
        },
        status_code=status_code,
    )


def _revisar_animal(request: Request, db: Session, user: User, animal_id: int):
    """Devuelve (animal, None) si se puede solicitar, o (None, redirección) si no."""
    animal = service.obtener_solicitable(db, animal_id)
    if animal is None:
        flash(request, "Ese animal no está disponible para adopción.", "error")
        return None, RedirectResponse("/animales", status_code=303)
    if service.tiene_pendiente(db, animal.id, user.id):
        flash(request, "Ya tienes una solicitud pendiente para este animal.", "error")
        return None, RedirectResponse("/mis-solicitudes", status_code=303)
    return animal, None


@router.get("/animales/{animal_id}/solicitar")
def solicitar_form(
    animal_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_adoptante),
):
    animal, redireccion = _revisar_animal(request, db, user, animal_id)
    if redireccion:
        return redireccion
    return _render_form(request, user, animal, {})


@router.post("/animales/{animal_id}/solicitar")
def solicitar(
    animal_id: int,
    request: Request,
    datos: dict = Depends(datos_formulario),
    db: Session = Depends(get_db),
    user: User = Depends(get_adoptante),
):
    animal, redireccion = _revisar_animal(request, db, user, animal_id)
    if redireccion:
        return redireccion

    errores = service.validar(datos)
    if errores:
        for error in errores:
            flash(request, error, "error")
        return _render_form(request, user, animal, datos, status_code=400)

    solicitud = service.crear(db, user, animal, datos)
    if solicitud is None:
        flash(request, "Ya tienes una solicitud pendiente para este animal.", "error")
        return RedirectResponse("/mis-solicitudes", status_code=303)

    flash(
        request,
        f"Solicitud enviada para «{animal.nombre}». La fundación la revisará pronto.",
        "success",
    )
    if correo_service.notificar("recibida", solicitud):
        flash(
            request,
            "Tu solicitud quedó registrada, pero no pudimos enviarte el correo de confirmación.",
            "warning",
        )
    return RedirectResponse("/mis-solicitudes", status_code=303)


@router.get("/mis-solicitudes")
def mis_solicitudes(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_adoptante),
):
    return templates.TemplateResponse(
        request,
        "solicitudes/mis_solicitudes.html",
        {"user": user, "solicitudes": service.listar_de_usuario(db, user)},
    )

@router.post("/solicitudes/{solicitud_id}/cancelar")
def cancelar(
    solicitud_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_adoptante),
):
    try:
        cancelar_propia(db, user, solicitud_id)
    except ReglaNegocio as error:
        flash(request, str(error), "error")
    else:
        flash(request, "Solicitud cancelada.", "success")
    return RedirectResponse("/mis-solicitudes", status_code=303)