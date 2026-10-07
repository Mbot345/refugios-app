from fastapi import APIRouter, Depends, Request

from app.core.deps import get_current_user
from app.core.templates import templates
from app.models.user import User

# dependencies=... protege TODAS las rutas de este router
router = APIRouter(prefix="/mascotas", dependencies=[Depends(get_current_user)])


@router.get("")
def lista(request: Request, user: User = Depends(get_current_user)):
    return templates.TemplateResponse(request, "mascotas/lista.html", {"user": user})