from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.flash import flash
from app.core.templates import templates
from app.services import auth_service, fundacion_service

router = APIRouter()


@router.get("/login")
def login_form(request: Request):
    if request.session.get("user_id"):
        return RedirectResponse("/", status_code=303)
    return templates.TemplateResponse(request, "auth/login.html")


@router.post("/login")
def login(request: Request, username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = auth_service.authenticate(db, username.strip(), password)
    if user is None:
        flash(request, "Credenciales incorrectas.", "error")
        return templates.TemplateResponse(request, "auth/login.html", {"username": username}, status_code=401)
    request.session.clear()
    request.session["user_id"] = user.id
    flash(request, f"Bienvenido, {user.username}.", "success")
    return RedirectResponse(auth_service.ruta_inicial(user), status_code=303)


def _render_registro(request: Request, db: Session, datos: dict, status_code: int = 200):
    provincia_id = datos.get("provincia_id", "")
    ciudades = fundacion_service.ciudades_de(db, int(provincia_id)) if provincia_id.isdigit() else []
    return templates.TemplateResponse(request, "auth/registro.html", {
        "datos": datos,
        "provincias": fundacion_service.listar_provincias(db),
        "ciudades": ciudades,
    }, status_code=status_code)


@router.get("/registro")
def registro_form(request: Request, db: Session = Depends(get_db)):
    return _render_registro(request, db, {})


@router.post("/registro")
def registro(
    request: Request,
    username: str = Form(...),
    nombres_completos: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    password2: str = Form(...),
    cedula: str = Form(...),
    telefono: str = Form(...),
    provincia_id: str = Form(...),
    ciudad_id: str = Form(...),
    direccion: str = Form(...),
    db: Session = Depends(get_db),
):
    datos = auth_service.normalizar_datos_registro({
        "username": username, "nombres_completos": nombres_completos,
        "email": email, "password": password, "password2": password2,
        "cedula": cedula, "telefono": telefono,
        "provincia_id": provincia_id, "ciudad_id": ciudad_id,
        "direccion": direccion,
    })
    errores = auth_service.validate_registration(db, datos)
    if errores:
        for error in errores:
            flash(request, error, "error")
        return _render_registro(request, db, datos, 400)

    try:
        auth_service.register_user(db, datos)
    except auth_service.RegistroDuplicado as exc:
        for error in exc.errores:
            flash(request, error, "error")
        return _render_registro(request, db, datos, 400)

    flash(request, "Cuenta creada. Ya puedes iniciar sesión.", "success")
    return RedirectResponse("/login", status_code=303)


@router.get("/registro/provincias/{provincia_id}/ciudades")
def ciudades_registro(provincia_id: int, db: Session = Depends(get_db)):
    return [
        {"id": ciudad.id, "nombre": ciudad.nombre}
        for ciudad in fundacion_service.ciudades_de(db, provincia_id)
    ]


@router.post("/logout")
def logout(request: Request):
    request.session.clear()
    flash(request, "Sesión cerrada.", "info")
    return RedirectResponse("/login", status_code=303)
