from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.core.constants import ESPECIES, SEXOS, TAMANOS
from app.core.database import get_db
from app.core.deps import get_gestor
from app.core.flash import flash
from app.core.templates import templates
from app.models.animal import Animal
from app.models.user import User
from app.services import animal_service as service

# Solo admin y trabajador (con fundación) pueden usar este router
router = APIRouter(prefix="/animales", dependencies=[Depends(get_gestor)])


def datos_formulario(
    nombre: str = Form(""),
    especie: str = Form(""),
    raza: str = Form(""),
    sexo: str = Form(""),
    tamano: str = Form(""),
    edad_meses: str = Form(""),
    estado_salud: str = Form(""),
    descripcion: str = Form(""),
    fundacion_id: str = Form(""),
) -> dict:
    return service.limpiar_datos(
        nombre, especie, raza, sexo, tamano, edad_meses,
        estado_salud, descripcion, fundacion_id,
    )


def _render_form(
    request: Request,
    db: Session,
    user: User,
    animal: Animal | None = None,
    datos: dict | None = None,
    status_code: int = 200,
):
    return templates.TemplateResponse(
        request,
        "animales/form.html",
        {
            "user": user,
            "animal": animal,
            "datos": datos or {},
            "fundaciones": service.listar_fundaciones(db, user),
            "especies": ESPECIES,
            "sexos": SEXOS,
            "tamanos": TAMANOS,
        },
        status_code=status_code,
    )


def _no_existe(request: Request):
    flash(request, "El animal no existe o no pertenece a tu fundación.", "error")
    return RedirectResponse("/animales", status_code=303)


# ---------- READ (lista) ----------
@router.get("")
def lista(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_gestor),
):
    return templates.TemplateResponse(
        request,
        "animales/lista.html",
        {"user": user, "animales": service.listar(db, user)},
    )


# ---------- CREATE ----------
@router.get("/nuevo")
def nuevo(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_gestor),
):
    return _render_form(request, db, user, datos={"estado_salud": "Sin evaluar"})


@router.post("")
def crear(
    request: Request,
    datos: dict = Depends(datos_formulario),
    db: Session = Depends(get_db),
    user: User = Depends(get_gestor),
):
    errores = service.validar(db, user, datos)
    if errores:
        for error in errores:
            flash(request, error, "error")
        return _render_form(request, db, user, datos=datos, status_code=400)

    animal = service.crear(db, user, datos)
    flash(request, f"Animal «{animal.nombre}» registrado.", "success")
    return RedirectResponse("/animales", status_code=303)


# ---------- UPDATE ----------
@router.get("/{animal_id}/editar")
def editar_form(
    animal_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_gestor),
):
    animal = service.obtener(db, animal_id, user)
    if animal is None:
        return _no_existe(request)
    return _render_form(request, db, user, animal=animal, datos=service.a_datos(animal))


@router.post("/{animal_id}/editar")
def editar(
    animal_id: int,
    request: Request,
    datos: dict = Depends(datos_formulario),
    db: Session = Depends(get_db),
    user: User = Depends(get_gestor),
):
    animal = service.obtener(db, animal_id, user)
    if animal is None:
        return _no_existe(request)

    errores = service.validar(db, user, datos)
    if errores:
        for error in errores:
            flash(request, error, "error")
        return _render_form(request, db, user, animal=animal, datos=datos, status_code=400)

    service.actualizar(db, user, animal, datos)
    flash(request, f"Animal «{animal.nombre}» actualizado.", "success")
    return RedirectResponse("/animales", status_code=303)


# ---------- DELETE ----------
@router.post("/{animal_id}/eliminar")
def eliminar(
    animal_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_gestor),
):
    animal = service.obtener(db, animal_id, user)
    if animal is None:
        return _no_existe(request)

    motivo = service.motivo_no_eliminable(animal)
    if motivo:
        flash(request, motivo, "error")
        return RedirectResponse("/animales", status_code=303)

    nombre = animal.nombre
    service.eliminar(db, animal)
    flash(request, f"Animal «{nombre}» eliminado.", "info")
    return RedirectResponse("/animales", status_code=303)