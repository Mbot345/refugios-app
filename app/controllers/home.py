from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse

from app.core.templates import templates

router = APIRouter()


@router.get("/")
def home(request: Request):
    if request.session.get("user_id"):
        return RedirectResponse("/mascotas", status_code=303)
    return templates.TemplateResponse(request, "home.html")