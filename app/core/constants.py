"""Valores permitidos de los campos de tipo catálogo."""

ROLES_GLOBALES = ("admin", "moderador")
ROLES_FUNDACION = (
    "admin_fundacion",
    "encargado_animales",
    "encargado_adopciones",
    "encargado_eventos",
)
ROLES = ROLES_GLOBALES + ROLES_FUNDACION + ("adoptante",)

ROL_ETIQUETAS = {
    "admin": "Administrador general",
    "moderador": "Moderador",
    "admin_fundacion": "Administrador de fundación",
    "encargado_animales": "Encargado de animales",
    "encargado_adopciones": "Encargado de adopciones",
    "encargado_eventos": "Encargado de eventos",
    "adoptante": "Adoptante",
}

TAMANOS = ("pequeño", "mediano", "grande")
ESPECIES = ("Perro", "Gato", "Otro")
SEXOS = ("Macho", "Hembra")

ESTADOS_ANIMAL = ("disponible", "en_proceso", "adoptado")
ESTADOS_SOLICITUD = ("pendiente", "aprobada", "rechazada", "cancelada", "finalizada")
TIPOS_REGISTRO_SANITARIO = ("vacuna", "desparasitación", "antecedente", "otro")