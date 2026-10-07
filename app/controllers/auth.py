import bcrypt
from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User

router = APIRouter()
templates = Jinja2Templates(directory="app/views")


@router.get("/login", name="login_form")
def login_form(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="auth/login.html",
        context={"error": None},
    )


@router.post("/login", name="login")
def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    user = db.scalar(
        select(User).where(or_(User.username == username, User.email == username))
    )
    valid = False
    if user and user.activo:
        try:
            valid = bcrypt.checkpw(password.encode(), user.password_hash.encode())
        except (ValueError, TypeError):
            valid = False
    if not valid:
        return templates.TemplateResponse(
            request=request,
            name="auth/login.html",
            context={"error": "Usuario o contraseña incorrectos."},
            status_code=400,
        )
    request.session["user_id"] = user.id
    request.session["flash"] = "Sesión iniciada correctamente."
    return RedirectResponse("/mascotas", status_code=303)


@router.post("/logout", name="logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/login", status_code=303)
