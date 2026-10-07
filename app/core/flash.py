from fastapi import Request


def flash(request: Request, message: str, category: str = "info") -> None:
    """Guarda un mensaje en la sesión para mostrarlo en la siguiente vista."""
    flashes = request.session.get("_flashes", [])
    flashes.append({"message": message, "category": category})
    request.session["_flashes"] = flashes


def pop_flashes(request: Request) -> list[dict]:
    """Devuelve los mensajes pendientes y los borra."""
    return request.session.pop("_flashes", [])