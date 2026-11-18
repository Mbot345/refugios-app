from fastapi import APIRouter, Depends, File, Form, Request, UploadFile
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from app.services import foto_service
from app.core.constants import ESPECIES, SEXOS, TAMANOS, TIPOS_REGISTRO_SANITARIO
from app.core.database import get_db
from app.core.deps import get_gestor
from app.core.flash import flash
from app.core.templates import templates
from app.models.animal import Animal
from app.models.user import User
from app.services import animal_service as service
from app.services import sanitario_service

# Solo administrador de fundación y encargado de animales (con fundación)
router = APIRouter(prefix="/fundacion/animales", dependencies=[Depends(get_gestor)])


def datos_formulario(
    nombre: str = Form(""),
    especie: str = Form(""),
    raza: str = Form(""),
    sexo: str = Form(""),
    tamano: str = Form(""),
    edad_meses: str = Form(""),
    estado_salud: str = Form(""),
    descripcion: str = Form(""),
) -> dict:
    return service.limpiar_datos(
        nombre, especie, raza, sexo, tamano, edad_meses, estado_salud, descripcion
    )


def _render_form(
    request: Request,
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
            "especies": ESPECIES,
            "sexos": SEXOS,
            "tamanos": TAMANOS,
            "tipos_sanitarios": TIPOS_REGISTRO_SANITARIO,
        },
        status_code=status_code,
    )


def _no_existe(request: Request):
    flash(request, "El animal no existe o no pertenece a tu fundación.", "error")
    return RedirectResponse("/fundacion/animales", status_code=303)


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
def nuevo(request: Request, user: User = Depends(get_gestor)):
    return _render_form(request, user, datos={"estado_salud": "Sin evaluar"})


@router.post("")
def crear(
    request: Request,
    datos: dict = Depends(datos_formulario),
    db: Session = Depends(get_db),
    user: User = Depends(get_gestor),
):
    errores = service.validar(user, datos)
    if errores:
        for error in errores:
            flash(request, error, "error")
        return _render_form(request, user, datos=datos, status_code=400)

    animal = service.crear(db, user, datos)
    flash(
        request,
        f"Animal «{animal.nombre}» registrado. Ahora puedes completar su información sanitaria y descargar su QR.",
        "success",
    )
    return RedirectResponse(f"/fundacion/animales/{animal.id}/editar", status_code=303)


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
    return _render_form(request, user, animal=animal, datos=service.a_datos(animal))


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

    errores = service.validar(user, datos)
    if errores:
        for error in errores:
            flash(request, error, "error")
        return _render_form(request, user, animal=animal, datos=datos, status_code=400)

    service.actualizar(db, user, animal, datos)
    flash(request, f"Animal «{animal.nombre}» actualizado.", "success")
    return RedirectResponse("/fundacion/animales", status_code=303)

# ---------- Fotografías ----------
def _volver_a_editar(animal: Animal):
    return RedirectResponse(f"/fundacion/animales/{animal.id}/editar", status_code=303)


@router.post("/{animal_id}/fotos")
def foto_subir(
    animal_id: int,
    request: Request,
    archivo: UploadFile | None = File(None),
    db: Session = Depends(get_db),
    user: User = Depends(get_gestor),
):
    animal = service.obtener(db, animal_id, user)
    if animal is None:
        return _no_existe(request)

    try:
        if archivo is None or not archivo.filename:
            raise ValueError("Selecciona una foto para subir.")
        # Se lee un byte de más para detectar archivos que superan el límite
        foto_service.agregar(db, user, animal, archivo.file.read(foto_service.MAX_BYTES + 1))
    except ValueError as error:
        flash(request, str(error), "error")
    else:
        flash(request, "Foto agregada.", "success")
    return _volver_a_editar(animal)


@router.post("/{animal_id}/fotos/{foto_id}/principal")
def foto_principal(
    animal_id: int,
    foto_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_gestor),
):
    animal = service.obtener(db, animal_id, user)
    if animal is None:
        return _no_existe(request)
    try:
        foto_service.marcar_principal(db, user, animal, foto_id)
    except ValueError as error:
        flash(request, str(error), "error")
    else:
        flash(request, "Foto principal actualizada.", "success")
    return _volver_a_editar(animal)


@router.post("/{animal_id}/fotos/{foto_id}/eliminar")
def foto_eliminar(
    animal_id: int,
    foto_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_gestor),
):
    animal = service.obtener(db, animal_id, user)
    if animal is None:
        return _no_existe(request)
    try:
        foto_service.eliminar(db, user, animal, foto_id)
    except ValueError as error:
        flash(request, str(error), "error")
    else:
        flash(request, "Foto eliminada.", "success")
    return _volver_a_editar(animal)

# ---------- Información sanitaria ----------
@router.post("/{animal_id}/sanitario")
def sanitario_agregar(
    animal_id: int,
    request: Request,
    tipo: str = Form(""),
    descripcion: str = Form(""),
    fecha: str = Form(""),
    db: Session = Depends(get_db),
    user: User = Depends(get_gestor),
):
    animal = service.obtener(db, animal_id, user)
    if animal is None:
        return _no_existe(request)

    datos = sanitario_service.limpiar(tipo, descripcion, fecha)
    errores = sanitario_service.validar(user, datos)
    if errores:
        for error in errores:
            flash(request, error, "error")
    else:
        sanitario_service.agregar(db, animal, datos)
        flash(request, "Registro sanitario agregado.", "success")
    return RedirectResponse(f"/fundacion/animales/{animal.id}/editar", status_code=303)


@router.post("/{animal_id}/sanitario/{registro_id}/eliminar")
def sanitario_eliminar(
    animal_id: int,
    registro_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_gestor),
):
    animal = service.obtener(db, animal_id, user)
    if animal is None:
        return _no_existe(request)

    if not user.fundacion.activa:
        flash(request, "Tu fundación está suspendida: solo puedes consultar la información.", "error")
    elif sanitario_service.eliminar(db, animal, registro_id):
        flash(request, "Registro sanitario eliminado.", "success")
    else:
        flash(request, "El registro no existe.", "error")
    return RedirectResponse(f"/fundacion/animales/{animal.id}/editar", status_code=303)

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
        return RedirectResponse("/fundacion/animales", status_code=303)

    nombre = animal.nombre
    service.eliminar(db, animal)
    flash(request, f"Animal «{nombre}» eliminado.", "info")
    return RedirectResponse("/animales", status_code=303)