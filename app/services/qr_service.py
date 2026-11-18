import io

import segno


def generar_png(contenido: str) -> bytes:
    """Genera la imagen PNG de un código QR con el texto o enlace indicado."""
    buffer = io.BytesIO()
    segno.make(contenido, error="m").save(buffer, kind="png", scale=8, border=3)
    return buffer.getvalue()