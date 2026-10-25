from fastapi import APIRouter, Depends, Request

from app.core.deps import get_optional_user
from app.core.templates import templates
from app.models.user import User

router = APIRouter()


@router.get("/")
def home(request: Request, user: User | None = Depends(get_optional_user)):
    return templates.TemplateResponse(request, "home.html", {"user": user})