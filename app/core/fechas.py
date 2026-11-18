from datetime import date, datetime, timedelta, timezone

ECUADOR = timezone(timedelta(hours=-5))


def hoy() -> date:
    """Fecha actual en Ecuador continental (UTC-5), aunque el servidor esté en UTC."""
    return datetime.now(ECUADOR).date()