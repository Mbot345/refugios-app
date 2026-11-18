import io

from PIL import Image, ImageOps, UnidentifiedImageError
from sqlalchemy import select
from sqlalchemy.orm import Session, undefer

from app.models.animal import Animal, FotoAnimal
from app.models.fundacion import Fundacion
from app.models.user import User

MAX_FOTOS = 4
MAX_BYTES = 3 * 1024 * 1024  # 3 MB por foto subida
LADO_MAXIMO = 1000  # px: la foto se reduce a este tamaño
FORMATOS_PERMITIDOS = {"JPEG", "PNG", "WEBP"}

# Protección contra imágenes "bomba" (muy pequeñas en archivo pero enormes al abrirlas)
Image.MAX_IMAGE_PIXELS = 40_000_000


def procesar(contenido: bytes) -> bytes:
    """Valida que sea una imagen real, la endereza, la reduce y la devuelve como JPEG."""
    try:
        with Image.open(io.BytesIO(contenido)) as imagen:
            if imagen.format not in FORMATOS_PERMITIDOS:
                raise ValueError("Formato no permitido. Usa una imagen JPG, PNG o WEBP.")

            imagen = ImageOps.exif_transpose(imagen)  # respeta la orientación de la cámara
            if imagen.mode in ("RGBA", "LA", "P"):
                imagen = imagen.convert("RGBA")
                fondo = Image.new("RGB", imagen.size, (255, 255, 255))
                fondo.paste(imagen, mask=imagen.getchannel("A"))
                imagen = fondo
            else:
                imagen = imagen.convert("RGB")

            imagen.thumbnail((LADO_MAXIMO, LADO_MAXIMO))
            salida = io.BytesIO()
            imagen.save(salida, format="JPEG", quality=80, optimize=True)
            return salida.getvalue()
    except (UnidentifiedImageError, Image.DecompressionBombError, OSError):
        raise ValueError("El archivo no es una imagen válida.")


def _exigir_fundacion_activa(user: User) -> None:
    if not user.fundacion.activa:
        raise ValueError("Tu fundación está suspendida: solo puedes consultar la información.")


def _de_animal(animal: Animal, foto_id: int) -> FotoAnimal:
    for foto in animal.fotos:
        if foto.id == foto_id:
            return foto
    raise ValueError("La foto no existe.")


def agregar(db: Session, user: User, animal: Animal, contenido: bytes) -> FotoAnimal:
    _exigir_fundacion_activa(user)
    if len(animal.fotos) >= MAX_FOTOS:
        raise ValueError(f"Cada animal puede tener como máximo {MAX_FOTOS} fotos.")
    if not contenido:
        raise ValueError("El archivo está vacío.")
    if len(contenido) > MAX_BYTES:
        raise ValueError("La foto supera los 3 MB. Elige una más liviana.")

    foto = FotoAnimal(
        datos=procesar(contenido),
        es_principal=not animal.fotos,  # la primera foto queda como principal
        animal_id=animal.id,
    )
    db.add(foto)
    db.commit()
    return foto


def marcar_principal(db: Session, user: User, animal: Animal, foto_id: int) -> None:
    _exigir_fundacion_activa(user)
    elegida = _de_animal(animal, foto_id)
    for foto in animal.fotos:
        foto.es_principal = foto.id == elegida.id
    db.commit()


def eliminar(db: Session, user: User, animal: Animal, foto_id: int) -> None:
    _exigir_fundacion_activa(user)
    foto = _de_animal(animal, foto_id)
    era_principal = foto.es_principal
    restantes = [f for f in animal.fotos if f.id != foto.id]

    db.delete(foto)
    if era_principal and restantes:
        restantes[0].es_principal = True  # otra foto toma su lugar
    db.commit()


def obtener_publica(db: Session, foto_id: int) -> FotoAnimal | None:
    """Foto (con sus datos) de un animal de una fundación activa."""
    consulta = (
        select(FotoAnimal)
        .join(FotoAnimal.animal)
        .join(Animal.fundacion)
        .options(undefer(FotoAnimal.datos))
        .where(FotoAnimal.id == foto_id, Fundacion.activa.is_(True))
    )
    return db.scalar(consulta)