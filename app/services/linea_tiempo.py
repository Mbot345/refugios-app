from app.core.fechas import a_hora_local


def _paso(titulo: str, situacion: str, fecha=None, detalle: str | None = None) -> dict:
    return {
        "titulo": titulo,
        "situacion": situacion,  # hecho | actual | pendiente | fallido | cancelado
        "fecha": a_hora_local(fecha),
        "detalle": detalle,
    }


def construir(solicitud) -> list[dict]:
    """Pasos de la línea de tiempo de una solicitud, calculados a partir de su historial."""
    hitos = {h.estado_nuevo: h for h in solicitud.historial}
    estado = solicitud.estado
    aprobada = hitos.get("aprobada")
    decision = aprobada or hitos.get("rechazada")
    cancelada = hitos.get("cancelada")

    pasos = [_paso("Solicitud enviada", "hecho", solicitud.fecha_solicitud)]

    # Cancelada por el adoptante antes de que la fundación decidiera
    if estado == "cancelada" and aprobada is None:
        pasos.append(_paso("Solicitud cancelada", "cancelado", cancelada.fecha, cancelada.observacion))
        return pasos

    if estado == "pendiente":
        pasos.append(_paso("Revisión de la fundación", "pendiente",
                           detalle="La fundación está revisando tu solicitud."))
        pasos.append(_paso("Solicitud aprobada", "pendiente",
                           detalle="Te avisaremos por correo cuando haya una decisión."))
        pasos.append(_paso("Adopción confirmada", "pendiente"))
    else:
        pasos.append(_paso("Revisión de la fundación", "hecho", decision.fecha if decision else None))

        if estado == "rechazada":
            pasos.append(_paso("Solicitud rechazada", "fallido", decision.fecha, decision.observacion))
            return pasos

        pasos.append(_paso("Solicitud aprobada", "hecho", aprobada.fecha, aprobada.observacion))
        if estado == "finalizada":
            final = hitos["finalizada"]
            pasos.append(_paso("Adopción confirmada", "hecho", final.fecha, final.observacion))
        elif estado == "cancelada":
            pasos.append(_paso("Solicitud cancelada", "cancelado", cancelada.fecha, cancelada.observacion))
        else:  # aprobada
            pasos.append(_paso("Adopción confirmada", "pendiente",
                               detalle="Se confirma cuando completes los trámites en la fundación."))

    for paso in pasos:  # el primer paso pendiente es el que está en curso
        if paso["situacion"] == "pendiente":
            paso["situacion"] = "actual"
            break
    return pasos