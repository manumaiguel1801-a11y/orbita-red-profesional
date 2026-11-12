"""Vista del perfil de otra persona (ventana emergente), con lo que se tiene en común y la acción de conectar."""
import streamlit as st

from orbita import usuarios as us
from ui import estilo, sesion
from ui.comun import ejecutar, refrescar
from ui.estilo import esc, icono, pill, pills

NIVEL_TXT = {1: "Básico", 2: "Inicial", 3: "Intermedio", 4: "Avanzado", 5: "Experto"}


def _grado_txt(p: dict) -> str:
    if p["conectados"]:
        return "Conexión directa"
    if p["grado"] is None:
        return "Fuera de tu red"
    return f"Conexión de {p['grado']}.º grado"


def resumen_en_comun(p: dict) -> str:
    """HTML con todo lo que el usuario actual comparte con la persona."""
    filas = []
    if p["contactos_en_comun"]:
        filas.append(("conexion", f"{len(p['contactos_en_comun'])} contacto(s) en común", pills(p["contactos_en_comun"], "ind")))
    hab = [h["habilidad"] for h in p["habilidades"] if h["compartida"]]
    if hab:
        filas.append(("habilidad", f"{len(hab)} habilidad(es) en común", pills(hab, "ok")))
    emp = [e["empresa"] for e in p["empresas"] if e["compartida"]]
    if emp:
        filas.append(("empresa", "Han trabajado en la misma empresa", pills(emp, "ok")))
    proy = [x["proyecto"] for x in p["proyectos"] if x["compartido"]]
    if proy:
        filas.append(("proyecto", "Comparten proyecto", pills(proy, "ok")))
    if not filas:
        return '<div class="ox-s">Aún no tienen contactos, habilidades, empresas ni proyectos en común.</div>'
    return "".join(f'<div style="margin:.35rem 0 .7rem"><div class="ox-s" style="display:flex;gap:.4rem;align-items:center;'
                   f'color:#D4D4D8;font-weight:600">{icono(ic, 15)}{esc(t)}</div><div class="ox-meta">{chips}</div></div>'
                   for ic, t, chips in filas)


def acciones(yo: str, p: dict, key: str) -> None:
    """Botón de conexión según el estado de la relación."""
    if p["id"] == yo:
        return
    if p["conectados"]:
        st.button("Conectados", icon=":material/check:", key=f"{key}_c", disabled=True, use_container_width=True)
    elif p["invitacion_enviada"]:
        if st.button("Cancelar invitación", icon=":material/close:", key=f"{key}_x", use_container_width=True):
            ejecutar(us.cancelar_invitacion, yo, p["id"], exito="Invitación cancelada"); refrescar(); st.rerun()
    elif p["invitacion_recibida"]:
        if st.button("Aceptar invitación", icon=":material/how_to_reg:", key=f"{key}_a", type="primary", use_container_width=True):
            ejecutar(us.aceptar_invitacion, yo, p["id"], exito="Ahora están conectados"); refrescar(); st.rerun()
    elif st.button("Conectar", icon=":material/person_add:", key=f"{key}_i", type="primary", use_container_width=True):
        if ejecutar(us.enviar_invitacion, yo, p["id"], exito="Invitación enviada"):
            refrescar(); st.rerun()


@st.dialog("Perfil profesional", width="large")
def ver_perfil(otro_id: str) -> None:
    yo = sesion.uid()
    p = us.perfil_publico(yo, otro_id)
    if not p:
        st.error("Este perfil ya no existe.")
        return
    actual = next((e for e in p["empresas"] if e["actual"]), None)
    meta = [("ubicacion", p["ciudad"] or "Sin ciudad"), ("conexion", _grado_txt(p)),
            ("usuarios", f"{p['total_conexiones']} conexiones"), ("reloj", f"{p['anios_experiencia'] or 0} {'año' if p['anios_experiencia'] == 1 else 'años'} de experiencia")]
    if p["nivel_educativo"]:
        meta.append(("birrete", p["nivel_educativo"]))
    estilo.html(estilo.tarjeta_persona(
        p["nombre"], (p["titular"] or "Sin titular") + (f" · {actual['empresa']}" if actual else ""),
        f'<div style="margin-top:.3rem">{estilo.badge_rol(p["rol"])}</div><div class="ox-meta">{pills(meta)}</div>', tam=72))

    st.write("")
    c1, c2 = st.columns([1.15, 1], gap="medium")
    with c1, st.container(border=True):
        estilo.html(f'<div class="ox-t" style="margin-bottom:.3rem">{icono("chispa", 17)} Lo que tienen en común</div>' + resumen_en_comun(p))
    with c2, st.container(border=True):
        estilo.html(f'<div class="ox-t" style="margin-bottom:.3rem">{icono("correo", 17)} Contacto</div>')
        if p["conectados"]:
            estilo.html(pills([("correo", p["email"] or "—"), ("chat", p["telefono"] or "Sin teléfono")]))
        else:
            st.caption("El correo y el teléfono se muestran cuando están conectados.")
        acciones(yo, p, f"dlg_{otro_id}")

    if p["resumen"]:
        estilo.seccion("Acerca de")
        st.write(p["resumen"])
    estilo.seccion("Habilidades")
    if p["habilidades"]:
        hab = sorted(p["habilidades"], key=lambda h: (not h["compartida"], -(h["nivel"] or 0)))
        estilo.html("".join(pill(f'{h["habilidad"]} · {NIVEL_TXT.get(h["nivel"], "")}', "ok" if h["compartida"] else "",
                                 "check" if h["compartida"] else None) for h in hab))
        st.caption("En verde, las habilidades que también tienes tú.")
    else:
        st.caption("Sin habilidades registradas.")
    a, b = st.columns(2, gap="medium")
    with a:
        estilo.seccion("Experiencia")
        if not p["empresas"]:
            st.caption("Sin experiencia registrada.")
        for e in sorted(p["empresas"], key=lambda e: (not e["actual"], -(e["desde"] or 0))):
            estilo.html(f'<div class="ox-row" style="margin:.45rem 0">{estilo.logo_empresa(e["empresa"])}<div>'
                        f'<div class="ox-t" style="font-size:.93rem">{esc(e["cargo"])}</div>'
                        f'<div class="ox-s">{esc(e["empresa"])} · desde {e["desde"]}{" · Actual" if e["actual"] else ""}</div></div></div>')
    with b:
        estilo.seccion("Proyectos")
        if not p["proyectos"]:
            st.caption("Sin proyectos.")
        estilo.html("".join(pill(f'{x["proyecto"]} · {x["rol"]}', "ok" if x["compartido"] else "ind", "proyecto")
                            for x in p["proyectos"]))


def boton_ver_perfil(otro_id: str, key: str) -> None:
    if st.button("Ver perfil", icon=":material/visibility:", key=key, use_container_width=True):
        ver_perfil(otro_id)


def _linea(ic: str, texto: str, chips: str = "") -> str:
    return (f'<div style="margin-top:.45rem"><div class="ox-s" style="display:flex;gap:.35rem;align-items:center">'
            f'{icono(ic, 14)}{esc(texto)}</div>{f"<div class=ox-meta>{chips}</div>" if chips else ""}</div>')


def detalle_sugerencia(r: dict) -> str:
    """Explica por qué se sugiere a la persona: contactos, habilidades, empresa y proyectos en común."""
    partes = []
    if r["comunes"]:
        extra = len(r["comunes"]) - 3
        partes.append(_linea("conexion", "Conocen a", pills(r["comunes"][:3], "ind") + (pills([f"+{extra}"]) if extra > 0 else "")))
    if r["habilidades_compartidas"]:
        partes.append(_linea("habilidad", "Habilidades en común", pills(r["habilidades_compartidas"], "ok")))
    if r["empresa_compartida"]:
        partes.append(_linea("empresa", "Trabajan en " + ", ".join(r["empresa_compartida"])))
    if r["proyectos_compartidos"]:
        partes.append(_linea("proyecto", "Proyecto: " + ", ".join(r["proyectos_compartidos"])))
    return "".join(partes)
