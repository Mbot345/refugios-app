from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.core.constants import ESTADOS_SOLICITUD
from app.core.database import get_db
from app.core.deps import get_adopciones
from app.core.flash import flash
from app.core.templates import templates
from app.models.user import User
from app.services import revision_service as service
from app.services.revision_service import ReglaNegocio

# Solo admin de fundación y encargado de adopciones; cada consulta se limita a su fundación
router = APIRouter(prefix="/fundacion/solicitudes", dependencies=[Depends(get_adopciones)])


@router.get("")
def lista(
    request: Request,
    estado: str = "",
    db: Session = Depends(get_db),
    user: User = Depends(get_adopciones),
):
    return templates.TemplateResponse(
        request,
        "fundacion/solicitudes_lista.html",
        {
            "user": user,
            "solicitudes": service.listar_de_fundacion(db, user.fundacion_id, estado),
            "estado": estado,
            "estados": list(ESTADOS_SOLICITUD),
        },
    )


@router.get("/{solicitud_id}")
def detalle(
    solicitud_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_adopciones),
):
    solicitud = service.obtener_de_fundacion(db, solicitud_id, user.fundacion_id)
    if solicitud is None:
        flash(request, "La solicitud no existe.", "error")
        return RedirectResponse("/fundacion/solicitudes", status_code=303)
    return templates.TemplateResponse(
        request,
        "fundacion/solicitud_detalle.html",
        {"user": user, "s": solicitud, "fundacion": user.fundacion},
    )


def _ejecutar(request, db, user, solicitud_id, accion, observacion, mensaje):
    """Corre una acción del servicio y vuelve al detalle con el resultado."""
    try:
        accion(db, user, solicitud_id, observacion)
    except ReglaNegocio as error:
        flash(request, str(error), "error")
    else:
        flash(request, mensaje, "success")
    return RedirectResponse(f"/fundacion/solicitudes/{solicitud_id}", status_code=303)


@router.post("/{solicitud_id}/aprobar")
def aprobar(
    solicitud_id: int,
    request: Request,
    observacion: str = Form(""),
    db: Session = Depends(get_db),
    user: User = Depends(get_adopciones),
):
    return _ejecutar(
        request, db, user, solicitud_id, service.aprobar, observacion,
        "Solicitud aprobada. El animal pasó a «en proceso» y las demás solicitudes pendientes se rechazaron.",
    )


@router.post("/{solicitud_id}/rechazar")
def rechazar(
    solicitud_id: int,
    request: Request,
    observacion: str = Form(""),
    db: Session = Depends(get_db),
    user: User = Depends(get_adopciones),
):
    return _ejecutar(
        request, db, user, solicitud_id, service.rechazar, observacion, "Solicitud rechazada."
    )


@router.post("/{solicitud_id}/revocar")
def revocar(
    solicitud_id: int,
    request: Request,
    observacion: str = Form(""),
    db: Session = Depends(get_db),
    user: User = Depends(get_adopciones),
):
    return _ejecutar(
        request, db, user, solicitud_id, service.revocar, observacion,
        "Aprobación revocada. El animal volvió a estar disponible.",
    )


@router.post("/{solicitud_id}/finalizar")
def finalizar(
    solicitud_id: int,
    request: Request,
    observacion: str = Form(""),
    db: Session = Depends(get_db),
    user: User = Depends(get_adopciones),
):
    return _ejecutar(
        request, db, user, solicitud_id, service.finalizar, observacion,
        "Adopción confirmada. El animal ahora figura como adoptado.",
    )