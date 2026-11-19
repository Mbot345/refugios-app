import html as html_lib
import logging
import re
import smtplib
from email.message import EmailMessage

from app.core.config import settings
from app.core.templates import templates
from app.services import aprobacion_pdf_service

log = logging.getLogger("correos")

ASUNTOS = {
    "recibida": "Recibimos tu solicitud de preadopción de {animal}",
    "aprobada": "Tu solicitud de preadopción de {animal} fue aprobada",
    "rechazada": "Resultado de tu solicitud de preadopción de {animal}",
    "revocada": "Tu aprobación de preadopción de {animal} fue revocada",
    "finalizada": "Adopción de {animal} confirmada",
}
PLANTILLAS = {tipo: f"correos/{tipo}.html" for tipo in ASUNTOS}


def _a_texto(html: str) -> str:
    """Versión de texto plano para clientes de correo que no muestran HTML."""
    texto = re.sub(r"(?s)<(style|head)>.*?</\1>", "", html)
    texto = re.sub(r"</(p|tr|li|h\d)>|<br\s*/?>", "\n", texto)
    texto = html_lib.unescape(re.sub(r"<[^>]+>", " ", texto))
    lineas = [" ".join(linea.split()) for linea in texto.splitlines()]
    return re.sub(r"\n{3,}", "\n\n", "\n".join(lineas)).strip()


def enviar(
    destino: str,
    asunto: str,
    html: str,
    adjuntos: list[tuple[str, bytes]] | None = None,
) -> bool:
    """Envía un correo (con adjuntos PDF opcionales). Devuelve False si falla, sin romper la acción."""
    adjuntos = adjuntos or []

    if not settings.SMTP_USER:
        print(f"[correo simulado] Para: {destino} | Asunto: {asunto}")
        for nombre, contenido in adjuntos:
            print(f"[adjunto] {nombre} ({len(contenido) // 1024} KB)")
        print(_a_texto(html))
        print("-" * 60)
        return True

    try:
        mensaje = EmailMessage()
        mensaje["Subject"] = asunto
        mensaje["From"] = settings.SMTP_FROM or settings.SMTP_USER
        mensaje["To"] = destino
        mensaje.set_content(_a_texto(html))
        mensaje.add_alternative(html, subtype="html")
        for nombre, contenido in adjuntos:
            mensaje.add_attachment(
                contenido, maintype="application", subtype="pdf", filename=nombre
            )

        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as servidor:
            servidor.starttls()
            servidor.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            servidor.send_message(mensaje)
    except (smtplib.SMTPException, OSError, ValueError):
        log.exception("No se pudo enviar el correo a %s", destino)
        return False
    return True


def notificar(tipo: str, resultado) -> int:
    """
    Envía el correo que corresponde a un evento y devuelve cuántos fallaron.
    Para 'aprobada', resultado es (solicitud aprobada, [solicitudes rechazadas automáticamente]).
    Para el resto, resultado es la solicitud.
    """
    if tipo == "aprobada":
        solicitud, rechazadas = resultado
        envios = [("aprobada", solicitud)] + [("rechazada", otra) for otra in rechazadas]
    else:
        envios = [(tipo, resultado)]

    fallidos = 0
    for tipo_correo, s in envios:
        adjuntos = []
        if tipo_correo == "aprobada":
            try:
                adjuntos.append(
                    (f"hoja-aprobacion-{s.id}.pdf", aprobacion_pdf_service.generar(s))
                )
            except Exception:  # pylint: disable=broad-exception-caught
                # Sin la hoja el correo se envía igual; el solicitante puede descargarla desde la app
                log.exception("No se pudo generar la hoja de aprobación de la solicitud %s", s.id)

        html = templates.env.get_template(PLANTILLAS[tipo_correo]).render(
            s=s, f=s.animal.fundacion, app_url=settings.APP_URL.rstrip("/")
        )
        asunto = ASUNTOS[tipo_correo].format(animal=s.animal.nombre)
        if not enviar(s.solicitante.email, asunto, html, adjuntos):
            fallidos += 1
    return fallidos