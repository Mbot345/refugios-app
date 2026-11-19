from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_panel
from app.core.flash import flash
from app.core.templates import templates
from app.models.fundacion import Fundacion
from app.models.user import User
from app.services import estadisticas_service

# Solo lectura para administrador general y moderador
router = APIRouter(prefix="/admin/fundaciones", dependencies=[Depends(get_panel)])


@router.get("/{fundacion_id}/estadisticas")
def estadisticas_fundacion(
    fundacion_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_panel),
):
    fundacion = db.get(Fundacion, fundacion_id)
    if fundacion is None:
        flash(request, "La fundación no existe.", "error")
        return RedirectResponse("/admin/fundaciones", status_code=303)

    return templates.TemplateResponse(
        request,
        "admin/fundacion_estadisticas.html",
        {
            "user": user,
            "fundacion": fundacion,
            "stats": estadisticas_service.de_fundacion(db, fundacion.id),
        },
    )