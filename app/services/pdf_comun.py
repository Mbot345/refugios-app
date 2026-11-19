import io
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader
from reportlab.platypus import Image, Paragraph, Table, TableStyle

VERDE = colors.HexColor("#2e9e5b")
GRIS = colors.HexColor("#6b7280")
GRIS_CLARO = colors.HexColor("#f1f5f9")
BORDE = colors.HexColor("#d1d5db")

_base = getSampleStyleSheet()
ESTILOS = {
    "normal": ParagraphStyle("normal", parent=_base["Normal"], fontName="Helvetica", fontSize=10, leading=14),
    "pequeno": ParagraphStyle("pequeno", parent=_base["Normal"], fontName="Helvetica", fontSize=8.5, leading=11, textColor=GRIS),
    "titulo": ParagraphStyle("titulo", parent=_base["Title"], fontName="Helvetica-Bold", fontSize=26, leading=30, alignment=0, spaceAfter=2),
    "subtitulo": ParagraphStyle("subtitulo", parent=_base["Heading2"], fontName="Helvetica-Bold", fontSize=12, leading=15, textColor=VERDE, spaceBefore=12, spaceAfter=5),
    "etiqueta": ParagraphStyle("etiqueta", parent=_base["Normal"], fontName="Helvetica-Bold", fontSize=9.5, leading=13, textColor=GRIS),
}


def seguro(texto) -> str:
    """Texto listo para un párrafo: sin etiquetas y solo con caracteres que la fuente soporta."""
    texto = "" if texto is None else str(texto)
    texto = texto.encode("cp1252", errors="replace").decode("cp1252")
    return escape(texto).replace("\n", "<br/>")


def parrafo(texto, estilo="normal") -> Paragraph:
    return Paragraph(seguro(texto), ESTILOS[estilo])


def imagen_ajustada(datos: bytes, ancho_max: float, alto_max: float) -> Image:
    """Imagen escalada para caber en el recuadro sin deformarse."""
    ancho, alto = ImageReader(io.BytesIO(datos)).getSize()
    escala = min(ancho_max / ancho, alto_max / alto)
    return Image(io.BytesIO(datos), width=ancho * escala, height=alto * escala)


def tabla_datos(filas: list[tuple[str, str]], ancho_etiqueta=3.6 * cm, ancho_valor=6.4 * cm) -> Table:
    tabla = Table(
        [[parrafo(k, "etiqueta"), parrafo(v)] for k, v in filas],
        colWidths=[ancho_etiqueta, ancho_valor],
    )
    tabla.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LINEBELOW", (0, 0), (-1, -1), 0.4, BORDE),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    return tabla

def marco_pagina(titulo_derecha: str, margen=1.8 * cm):
    """Devuelve la función que dibuja la franja superior y el pie de cada página."""
    from datetime import datetime

    from reportlab.lib.pagesizes import A4

    from app.core.fechas import ECUADOR

    def dibujar(canvas, doc):
        ancho, alto = A4
        canvas.saveState()
        canvas.setFillColor(VERDE)
        canvas.rect(0, alto - 1.5 * cm, ancho, 1.5 * cm, stroke=0, fill=1)
        canvas.setFillColorRGB(1, 1, 1)
        canvas.setFont("Helvetica-Bold", 13)
        canvas.drawString(margen, alto - 0.95 * cm, "Refugios App")
        canvas.setFont("Helvetica", 11)
        canvas.drawRightString(ancho - margen, alto - 0.95 * cm, titulo_derecha)

        canvas.setFillColor(GRIS)
        canvas.setFont("Helvetica", 8)
        generado = datetime.now(ECUADOR).strftime("%d/%m/%Y %H:%M")
        canvas.drawString(margen, 1.1 * cm, f"Documento generado el {generado} (hora de Ecuador)")
        canvas.drawRightString(ancho - margen, 1.1 * cm, f"Página {doc.page}")
        canvas.restoreState()

    return dibujar