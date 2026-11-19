from datetime import date, datetime, timedelta, timezone

ECUADOR = timezone(timedelta(hours=-5))


def hoy() -> date:
    """Fecha actual en Ecuador continental (UTC-5), aunque el servidor esté en UTC."""
    return datetime.now(ECUADOR).date()

def a_hora_local(fecha: datetime | None) -> datetime | None:
    """Convierte una fecha guardada (UTC) a la hora de Ecuador."""
    if fecha is None:
        return None
    if fecha.tzinfo is None:
        fecha = fecha.replace(tzinfo=timezone.utc)
    return fecha.astimezone(ECUADOR)