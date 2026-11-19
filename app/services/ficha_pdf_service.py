import io
from datetime import datetime

import segno
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.platypus import Image, KeepTogether, SimpleDocTemplate, Spacer, Table, TableStyle

from app.core.fechas import ECUADOR
from app.services.pdf_comun import (
    BORDE, GRIS, GRIS_CLARO, VERDE, imagen_ajustada, parrafo, tabla_datos,
)

MARGEN = 1.8 * cm


def _formato_edad(meses):
    if meses is None:
        return "No registrada"
    anios, resto = divmod(meses, 12)
    partes = []
    if anios:
        partes.append(f"{anios} año" + ("s" if anios != 1 else ""))
    if resto or not anios:
        partes.append(f"{resto} mes" + ("es" if resto != 1 else ""))
    return " y ".join(partes)


def _qr_png(contenido: str) -> bytes:
    buffer = io.BytesIO()
    segno.make(contenido, error="m").save(buffer, kind="png", scale=6, border=2)
    return buffer.getvalue()


def _marco(canvas, doc):
    """Franja superior y pie de cada página."""
    ancho, alto = A4
    canvas.saveState()
    canvas.setFillColor(VERDE)
    canvas.rect(0, alto - 1.5 * cm, ancho, 1.5 * cm, stroke=0, fill=1)
    canvas.setFillColorRGB(1, 1, 1)
    canvas.setFont("Helvetica-Bold", 13)
    canvas.drawString(MARGEN, alto - 0.95 * cm, "Refugios App")
    canvas.setFont("Helvetica", 11)
    canvas.drawRightString(ancho - MARGEN, alto - 0.95 * cm, "Ficha técnica del animal")

    canvas.setFillColor(GRIS)
    canvas.setFont("Helvetica", 8)
    generado = datetime.now(ECUADOR).strftime("%d/%m/%Y %H:%M")
    canvas.drawString(MARGEN, 1.1 * cm, f"Documento generado el {generado} (hora de Ecuador)")
    canvas.drawRightString(ancho - MARGEN, 1.1 * cm, f"Página {doc.page}")
    canvas.restoreState()


def generar(animal, enlace_qr: str) -> bytes:
    """PDF con la ficha técnica de un animal (datos, fotos, información sanitaria y QR)."""
    fundacion = animal.fundacion
    fotos = sorted(animal.fotos, key=lambda f: f.id)
    principal = next((f for f in fotos if f.es_principal), fotos[0] if fotos else None)
    otras = [f for f in fotos if f is not principal][:3]

    contenido = []

    # --- Nombre y estado ---
    contenido.append(parrafo(animal.nombre, "titulo"))
    contenido.append(parrafo(
        f"Estado: {animal.estado.replace('_', ' ').capitalize()}  ·  {fundacion.nombre}", "pequeno"))
    contenido.append(Spacer(1, 0.4 * cm))

    # --- Foto principal + datos ---
    if principal:
        foto = imagen_ajustada(principal.datos, 7.2 * cm, 7.2 * cm)
    else:
        foto = Table([[parrafo("Sin fotografía", "pequeno")]], colWidths=[7.2 * cm], rowHeights=[5 * cm])
        foto.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), GRIS_CLARO),
                                  ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                                  ("ALIGN", (0, 0), (-1, -1), "CENTER")]))

    ciudad = getattr(fundacion, "ciudad", None)
    ubicacion = fundacion.nombre
    if ciudad is not None:
        ubicacion = f"{ciudad.nombre}, {ciudad.provincia.nombre}"

    datos = tabla_datos([
        ("Especie", animal.especie.capitalize()),
        ("Raza", animal.raza or "No registrada"),
        ("Sexo", animal.sexo.capitalize()),
        ("Tamaño", animal.tamano.capitalize()),
        ("Edad aproximada", _formato_edad(animal.edad_meses)),
        ("Estado de salud", animal.estado_salud),
        ("Ubicación", ubicacion),
    ], ancho_etiqueta=3.4 * cm, ancho_valor=6.0 * cm)

    cabecera = Table([[foto, datos]], colWidths=[7.8 * cm, 9.6 * cm])
    cabecera.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"),
                                  ("LEFTPADDING", (0, 0), (-1, -1), 0)]))
    contenido.append(cabecera)

    # --- Otras fotos ---
    if otras:
        miniaturas = [imagen_ajustada(f.datos, 4.6 * cm, 3.4 * cm) for f in otras]
        fila = Table([miniaturas], colWidths=[4.9 * cm] * len(miniaturas), hAlign="LEFT")
        fila.setStyle(TableStyle([("LEFTPADDING", (0, 0), (-1, -1), 0), ("VALIGN", (0, 0), (-1, -1), "TOP")]))
        contenido.append(Spacer(1, 0.3 * cm))
        contenido.append(fila)

    # --- Descripción ---
    contenido.append(parrafo("Descripción", "subtitulo"))
    contenido.append(parrafo(animal.descripcion or "Sin descripción registrada."))

    # --- Información sanitaria ---
    contenido.append(parrafo("Información sanitaria", "subtitulo"))
    registros = sorted(animal.registros_sanitarios, key=lambda r: r.fecha, reverse=True)
    if registros:
        filas = [[parrafo("Fecha", "etiqueta"), parrafo("Tipo", "etiqueta"), parrafo("Descripción", "etiqueta")]]
        for r in registros:
            filas.append([parrafo(r.fecha.strftime("%d/%m/%Y")), parrafo(r.tipo.capitalize()), parrafo(r.descripcion)])
        tabla = Table(filas, colWidths=[2.6 * cm, 3.2 * cm, 11.6 * cm], repeatRows=1)
        tabla.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), GRIS_CLARO),
            ("LINEBELOW", (0, 0), (-1, -1), 0.4, BORDE),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        contenido.append(tabla)
    else:
        contenido.append(parrafo("Aún no hay registros sanitarios.", "pequeno"))

    # --- QR y contacto ---
    qr = Image(io.BytesIO(_qr_png(enlace_qr)), width=3 * cm, height=3 * cm)
    pie = Table(
        [[qr, [parrafo("Contacto de la fundación", "subtitulo"),
               parrafo(fundacion.nombre),
               parrafo(fundacion.direccion or "", "pequeno"),
               parrafo(f"Correo: {fundacion.email_contacto}" +
                       (f"   ·   Tel.: {fundacion.telefono}" if fundacion.telefono else "")),
               parrafo("Escanea el código QR para abrir esta ficha desde tu celular.", "pequeno")]]],
        colWidths=[3.4 * cm, 14 * cm],
    )
    pie.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                             ("LEFTPADDING", (0, 0), (-1, -1), 0),
                             ("BOX", (0, 0), (-1, -1), 0.4, BORDE),
                             ("LEFTPADDING", (1, 0), (1, 0), 10)]))
    contenido.append(Spacer(1, 0.5 * cm))
    contenido.append(KeepTogether(pie))

    salida = io.BytesIO()
    SimpleDocTemplate(
        salida, pagesize=A4, leftMargin=MARGEN, rightMargin=MARGEN,
        topMargin=2.4 * cm, bottomMargin=1.8 * cm,
        title=f"Ficha técnica - {animal.nombre}", author="Refugios App",
    ).build(contenido, onFirstPage=_marco, onLaterPages=_marco)
    return salida.getvalue()