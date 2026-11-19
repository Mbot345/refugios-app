import io

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.platypus import KeepTogether, SimpleDocTemplate, Spacer, Table, TableStyle

from app.core.fechas import a_hora_local
from app.services.pdf_comun import (
    BORDE, GRIS_CLARO, imagen_ajustada, marco_pagina, parrafo, tabla_datos,
)

MARGEN = 1.8 * cm

DOCUMENTOS = [
    "Copia de tu cédula de ciudadanía.",
    "Copia de la planilla de un servicio básico (agua, luz o teléfono) reciente.",
]


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


def _foto_principal(animal):
    fotos = sorted(animal.fotos, key=lambda f: f.id)
    return next((f for f in fotos if f.es_principal), fotos[0] if fotos else None)


def generar(solicitud) -> bytes:
    """Hoja de aprobación de preadopción lista para imprimir y presentar en la fundación."""
    animal = solicitud.animal
    fundacion = animal.fundacion
    aprobacion = next((h for h in solicitud.historial if h.estado_nuevo == "aprobada"), None)
    fecha_aprobacion = a_hora_local(aprobacion.fecha).strftime("%d/%m/%Y") if aprobacion else "—"
    observacion = aprobacion.observacion if aprobacion else None

    contenido = []
    contenido.append(parrafo("Hoja de aprobación", "titulo"))
    contenido.append(parrafo(
        f"Solicitud N.º {solicitud.id}  ·  Aprobada el {fecha_aprobacion}  ·  {fundacion.nombre}", "pequeno"))
    contenido.append(Spacer(1, 0.4 * cm))

    # --- Animal: foto + datos ---
    principal = _foto_principal(animal)
    if principal:
        foto = imagen_ajustada(principal.datos, 5.6 * cm, 5.6 * cm)
    else:
        foto = Table([[parrafo("Sin fotografía", "pequeno")]], colWidths=[5.6 * cm], rowHeights=[4 * cm])
        foto.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), GRIS_CLARO),
                                  ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                                  ("ALIGN", (0, 0), (-1, -1), "CENTER")]))
    datos_animal = tabla_datos([
        ("Nombre", animal.nombre),
        ("Especie", animal.especie.capitalize()),
        ("Raza", animal.raza or "No registrada"),
        ("Sexo", animal.sexo.capitalize()),
        ("Tamaño", animal.tamano.capitalize()),
        ("Edad aproximada", _formato_edad(animal.edad_meses)),
    ], ancho_etiqueta=3.4 * cm, ancho_valor=7.6 * cm)

    contenido.append(parrafo("Datos del animal", "subtitulo"))
    animal_tabla = Table([[foto, datos_animal]], colWidths=[6.2 * cm, 11.2 * cm])
    animal_tabla.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"),
                                      ("LEFTPADDING", (0, 0), (-1, -1), 0)]))
    contenido.append(animal_tabla)

    # --- Adoptante ---
    contenido.append(parrafo("Datos del adoptante", "subtitulo"))
    contenido.append(tabla_datos([
        ("Nombres y apellidos", solicitud.nombres_completos),
        ("Cédula de ciudadanía", solicitud.cedula),
        ("Correo electrónico", solicitud.solicitante.email),
    ], ancho_etiqueta=4.4 * cm, ancho_valor=13 * cm))

    if observacion:
        contenido.append(parrafo("Observación de la fundación", "subtitulo"))
        contenido.append(parrafo(observacion))

    # --- Documentos a presentar ---
    contenido.append(parrafo("Documentos que debes presentar", "subtitulo"))
    contenido.append(parrafo(
        "Imprime esta hoja y preséntala en la fundación junto con los siguientes documentos:"))
    contenido.append(Spacer(1, 0.15 * cm))
    for documento in DOCUMENTOS:
        contenido.append(parrafo(f"•  {documento}"))

    # --- Contacto ---
    contenido.append(parrafo("Dónde presentarlos", "subtitulo"))
    lineas = [fundacion.nombre, fundacion.direccion or "", f"Correo: {fundacion.email_contacto}"]
    if fundacion.telefono:
        lineas.append(f"Teléfono: {fundacion.telefono}")
    for linea in lineas:
        contenido.append(parrafo(linea))

    # --- Firmas ---
    firmas = Table(
        [[parrafo("Firma del adoptante", "pequeno"), "", parrafo("Firma y sello de la fundación", "pequeno")]],
        colWidths=[7.4 * cm, 2.6 * cm, 7.4 * cm], rowHeights=[1.1 * cm],
    )
    firmas.setStyle(TableStyle([("LINEABOVE", (0, 0), (0, 0), 0.6, BORDE),
                                ("LINEABOVE", (2, 0), (2, 0), 0.6, BORDE),
                                ("VALIGN", (0, 0), (-1, -1), "BOTTOM")]))
    contenido.append(Spacer(1, 1.6 * cm))
    contenido.append(KeepTogether(firmas))
    contenido.append(Spacer(1, 0.4 * cm))
    contenido.append(parrafo(
        "Esta hoja acredita la aprobación de la preadopción; la adopción se concreta cuando la "
        "fundación la confirma tras revisar los documentos.", "pequeno"))

    salida = io.BytesIO()
    SimpleDocTemplate(
        salida, pagesize=A4, leftMargin=MARGEN, rightMargin=MARGEN,
        topMargin=2.4 * cm, bottomMargin=1.8 * cm,
        title=f"Hoja de aprobación - Solicitud {solicitud.id}", author="Refugios App",
    ).build(contenido,
            onFirstPage=marco_pagina("Hoja de aprobación de preadopción"),
            onLaterPages=marco_pagina("Hoja de aprobación de preadopción"))
    return salida.getvalue()