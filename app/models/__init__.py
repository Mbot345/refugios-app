from app.models.user import User
from app.models.fundacion import Fundacion
from app.models.animal import Animal, FotoAnimal, RegistroSanitario
from app.models.solicitud import SolicitudPreadopcion, HistorialSolicitud

__all__ = [
    "User",
    "Fundacion",
    "Animal",
    "FotoAnimal",
    "RegistroSanitario",
    "SolicitudPreadopcion",
    "HistorialSolicitud",
]