"""Inicio: panel personal del usuario autenticado."""
from datetime import datetime

import plotly.express as px
import streamlit as st

from orbita import analitica, catalogo, recomendaciones as rec, usuarios as us
from ui import estilo, rutas, sesion
from ui.comun import ejecutar, refrescar
from ui.estilo import esc, pills
from ui.perfil_publico import boton_ver_perfil, detalle_sugerencia


def completitud(p: dict) -> tuple[int, list[tuple[str, bool]]]:
    u = p["usuario"]
    pasos = [
        ("Titular profesional", bool(u.get("titular"))),
        ("Ciudad", bool(u.get("ciudad"))),
        ("Resumen profesional", len(u.get("resumen") or "") >= 30),
        ("Teléfono de contacto", bool(u.get("telefono"))),
        ("Al menos 3 habilidades", len(p["habilidades"]) >= 3),
        ("Experiencia laboral", len(p["empresas"]) >= 1),
        ("Participación en un proyecto", len(p["proyectos"]) >= 1),
        ("Al menos 3 conexiones", len(p["conexiones"]) >= 3),
    ]
    return round(100 * sum(ok for _, ok in pasos) / len(pasos)), pasos


def _saludo() -> str:
    h = datetime.now().hour
    return "Buenos días" if h < 12 else "Buenas tardes" if h < 19 else "Buenas noches"


def pagina():
    yo = sesion.usuario()
    if (msg := st.session_state.pop("bienvenida", None)):
        st.toast(msg, icon=":material/waving_hand:")
    p = us.obtener_usuario(yo["id"])
    if not p:
        st.error("Su cuenta ya no existe."); sesion.cerrar(); st.rerun()
    pct, pasos = completitud(p)
    invit = us.invitaciones_recibidas(yo["id"])
    empleos = rec.recomendar_empleos(yo["id"], 3)
    empresa = next((e["empresa"] for e in p["empresas"] if e["actual"]), None)

    linea = []
    if invit:
        linea.append(f"tienes <b>{len(invit)}</b> invitación(es) de conexión")
    if empleos:
        linea.append(f"hay <b>{len(empleos)}</b> empleos recomendados para ti")
    estilo.html(f"""<div class="ox-hero"><div class="ox-row" style="align-items:center">
        {estilo.avatar(yo['nombre'], 64)}
        <div style="flex:1"><h2>{_saludo()}, {esc(yo['nombre'].split()[0])}</h2>
        <p>{esc(p['usuario'].get('titular') or 'Completa tu titular profesional')}{' · ' + esc(empresa) if empresa else ''}
        &nbsp;{estilo.badge_rol(yo['rol'])}</p>
        <p style="margin-top:.5rem;font-size:.92rem">{(' y '.join(linea).capitalize() + '.') if linea else 'Tu red está al día.'}</p></div>
        <div style="text-align:center">{estilo.anillo(pct)}<div style="font-size:.75rem;color:#E9D5FF;margin-top:.25rem">Perfil completo</div></div>
        </div></div>""")

    c = st.columns(4)
    estilo.stat(c[0], len(p["conexiones"]), "Conexiones", "conexion", "violeta")
    estilo.stat(c[1], len(p["habilidades"]), "Habilidades", "habilidad", "naranja")
    estilo.stat(c[2], len(p["postulaciones"]), "Postulaciones", "enviar", "lima")
    estilo.stat(c[3], len(invit), "Invitaciones pendientes", "campana", "rosa")

    izq, der = st.columns([1.75, 1], gap="large")
    with izq:
        if sesion.es_reclutador() and not sesion.es_admin():
            _resumen_reclutador(yo["id"])
        estilo.seccion("Empleos recomendados para ti")
        if not empleos:
            estilo.vacio("maletin", "Aún no hay empleos que coincidan", "Agrega habilidades a tu perfil para recibir recomendaciones.")
        for o in empleos:
            with st.container(border=True):
                estilo.html(estilo.tarjeta_oferta(
                    o["oferta"], o["empresa"], [("ubicacion", o['ciudad']), ("maletin", o["modalidad"])],
                    '<div class="ox-meta">' + estilo.pills_ok(o["cumple"])
                    + estilo.pills_no(o["faltan"]) + "</div>",
                    estilo.anillo(o["puntaje"])))
                if st.button("Postularme", key=f"ini_pos_{o['oferta_id']}", type="primary"):
                    if ejecutar(us.postular, yo["id"], o["oferta_id"], exito="Postulación enviada"):
                        refrescar(); st.rerun()
        estilo.seccion("Personas que quizá conozcas")
        personas = rec.recomendar_contactos(yo["id"], 4)
        enviadas = {i["id"] for i in us.invitaciones_enviadas(yo["id"])}
        if not personas:
            estilo.vacio("brujula", "Sin sugerencias por ahora", "Agrega habilidades o conexiones para descubrir personas.")
        cols = st.columns(2)
        for i, r in enumerate(personas):
            with cols[i % 2], st.container(border=True):
                estilo.html(estilo.tarjeta_persona(r["nombre"], r["titular"], detalle_sugerencia(r)))
                # (ya hay dos niveles de columnas: los botones se apilan en lugar de usar columnas)
                boton_ver_perfil(r["id"], f"ini_v_{r['id']}")
                if r["id"] in enviadas:
                    st.button("Pendiente", icon=":material/schedule:", key=f"ini_c_{r['id']}", disabled=True, use_container_width=True)
                elif st.button("Conectar", icon=":material/person_add:", key=f"ini_c_{r['id']}", type="primary", use_container_width=True):
                    ejecutar(us.enviar_invitacion, yo["id"], r["id"], exito="Invitación enviada"); refrescar(); st.rerun()

    with der:
        with st.container(border=True):
            estilo.html(f'<div class="ox-t">Fortaleza del perfil · {pct}%</div>{estilo.barra(pct)}')
            for nombre, ok in pasos:
                estilo.html(f'<div class="ox-check"><span class="d" style="background:{"#A3E635" if ok else "#3F3F46"}">'
                            f'{estilo.icono("check", 13, grosor=3) if ok else ""}</span>{esc(nombre)}</div>')
            if pct < 100:
                rutas.enlace("perfil", "Completar mi perfil", ":material/arrow_forward:")
        if invit:
            with st.container(border=True):
                estilo.html('<div class="ox-t">' + estilo.icono("campana") + ' Invitaciones</div>')
                for i in invit[:3]:
                    estilo.html(estilo.tarjeta_persona(i["nombre"], i["titular"], tam=38))
                    boton_ver_perfil(i["id"], f"ini_vi_{i['id']}")
                    a, b = st.columns(2)
                    if a.button("Aceptar", key=f"ini_ac_{i['id']}", type="primary", use_container_width=True):
                        ejecutar(us.aceptar_invitacion, yo["id"], i["id"], exito="Ahora están conectados"); refrescar(); st.rerun()
                    if b.button("Ignorar", key=f"ini_ig_{i['id']}", use_container_width=True):
                        ejecutar(us.rechazar_invitacion, yo["id"], i["id"]); refrescar(); st.rerun()
        with st.container(border=True):
            estilo.html('<div class="ox-t">' + estilo.icono("tendencia") + ' Habilidades más demandadas</div>')
            mias = {h["habilidad"] for h in p["habilidades"]}
            for h in analitica.habilidades_demandadas(6):
                tengo = h["habilidad"] in mias
                estilo.html(f'<div class="ox-check"><span class="d" style="background:{"#A3E635" if tengo else "#27272A"}">'
                            f'{estilo.icono("check", 13, grosor=3) if tengo else ""}</span><span style="flex:1">{esc(h["habilidad"])}</span>'
                            f'<span class="ox-pill">{h["ofertas"]} ofertas</span></div>')

    if sesion.es_admin():
        _resumen_plataforma()


def _resumen_reclutador(uid: str):
    empresas = catalogo.empresas_actuales(uid)
    if not empresas:
        st.warning("Tu rol es reclutador, pero no tienes una empresa actual en tu perfil. Agrégala en Mi perfil → Experiencia.")
        return
    estilo.seccion(f"Tu empresa · {empresas[0]['nombre']}")
    ofertas = catalogo.listar_ofertas(False, empresas[0]["id"])
    c = st.columns(3)
    estilo.stat(c[0], sum(o["activa"] for o in ofertas), "Ofertas activas", "maletin", "cian")
    estilo.stat(c[1], sum(o["postulantes"] for o in ofertas), "Postulantes", "usuarios", "lima")
    estilo.stat(c[2], len(ofertas), "Ofertas publicadas", "lista", "violeta")


def _resumen_plataforma():
    estilo.seccion("Resumen de la plataforma (administrador)")
    r = analitica.resumen()
    c = st.columns(4)
    estilo.stat(c[0], r["usuarios"], "Usuarios", "usuarios"); estilo.stat(c[1], r["empresas"], "Empresas", "empresa", "cian")
    estilo.stat(c[2], r["ofertas_activas"], "Ofertas activas", "maletin", "lima"); estilo.stat(c[3], r["relaciones"], "Relaciones", "red", "rosa")
    dem = analitica.habilidades_demandadas(10)
    if dem:
        fig = px.bar(dem[::-1], x="ofertas", y="habilidad", orientation="h", color="categoria",
                     labels={"ofertas": "Ofertas", "habilidad": "", "categoria": ""})
        fig.update_layout(height=320, margin=dict(l=0, r=0, t=10, b=0), legend=dict(orientation="h", y=-0.2))
        st.plotly_chart(fig, use_container_width=True)
