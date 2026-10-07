from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.flash import flash
from app.core.templates import templates
from app.services import auth_service

router = APIRouter()


@router.get("/login")
def login_form(request: Request):
    if request.session.get("user_id"):
        return RedirectResponse("/mascotas", status_code=303)
    return templates.TemplateResponse(request, "auth/login.html")


@router.post("/login")
def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    user = auth_service.authenticate(db, username.strip(), password)
    if user is None:
        flash(request, "Credenciales incorrectas.", "error")
        return templates.TemplateResponse(
            request, "auth/login.html", {"username": username}, status_code=401
        )

    request.session.clear()
    request.session["user_id"] = user.id
    flash(request, f"Bienvenido, {user.username}.", "success")
    return RedirectResponse("/mascotas", status_code=303)


@router.get("/registro")
def registro_form(request: Request):
    return templates.TemplateResponse(request, "auth/registro.html")


@router.post("/registro")
def registro(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    password2: str = Form(...),
    db: Session = Depends(get_db),
):
    username = username.strip()
    email = email.strip().lower()

    errors = auth_service.validate_registration(db, username, email, password, password2)
    if errors:
        for error in errors:
            flash(request, error, "error")
        return templates.TemplateResponse(
            request,
            "auth/registro.html",
            {"username": username, "email": email},
            status_code=400,
        )

    auth_service.register_user(db, username, email, password)
    flash(request, "Cuenta creada. Ya puedes iniciar sesión.", "success")
    return RedirectResponse("/login", status_code=303)


@router.post("/logout")
def logout(request: Request):
    request.session.clear()
    flash(request, "Sesión cerrada.", "info")
    return RedirectResponse("/login", status_code=303)