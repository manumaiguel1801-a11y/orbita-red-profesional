"""Mi red: invitaciones, conexiones, descubrir personas, contactos en común y mi grafo."""
import streamlit as st

from orbita import grafo_visual as gv
from orbita import recomendaciones as rec
from orbita import red
from orbita import usuarios as us
from ui import estilo, sesion
from ui.comun import ejecutar, grafo, leyenda, opciones_usuarios, refrescar
from ui.estilo import esc, icono, pills
from ui.perfil_publico import boton_ver_perfil, detalle_sugerencia


def _boton_conectar(yo: str, otro: str, conectados: set, enviadas: set, recibidas: set, key: str):
    if otro == yo:
        st.button("Tú", key=key, disabled=True, use_container_width=True)
    elif otro in conectados:
        st.button("Conectados", icon=":material/check:", key=key, disabled=True, use_container_width=True)
    elif otro in enviadas:
        st.button("Pendiente", icon=":material/schedule:", key=key, disabled=True, use_container_width=True)
    elif otro in recibidas:
        if st.button("Aceptar", icon=":material/how_to_reg:", key=key, type="primary", use_container_width=True):
            ejecutar(us.aceptar_invitacion, yo, otro, exito="Ahora están conectados"); refrescar(); st.rerun()
    elif st.button("Conectar", icon=":material/person_add:", key=key, type="primary", use_container_width=True):
        r = ejecutar(us.enviar_invitacion, yo, otro)
        if r:
            st.toast({"enviada": "Invitación enviada", "conectados": "Ahora están conectados",
                      "ya_conectados": "Ya estaban conectados"}[r], icon=":material/group_add:")
            refrescar(); st.rerun()


def _acciones(yo: str, otro: str, conectados: set, env: set, rec_: set, key: str):
    a, b = st.columns(2)
    with a:
        boton_ver_perfil(otro, f"{key}_v")
    with b:
        _boton_conectar(yo, otro, conectados, env, rec_, f"{key}_c")


def pagina():
    yo = sesion.uid()
    p = us.obtener_usuario(yo)
    recibidas = us.invitaciones_recibidas(yo)
    enviadas = us.invitaciones_enviadas(yo)
    conectados = {c["id"] for c in p["conexiones"]}
    ids_env, ids_rec = {e["id"] for e in enviadas}, {r["id"] for r in recibidas}
    estilo.encabezado("Mi red", f"{len(conectados)} conexiones · {len(recibidas)} invitaciones pendientes", "conexion")

    t = st.tabs([f"Invitaciones ({len(recibidas)})", f"Mis conexiones ({len(conectados)})", "Descubrir personas",
                 "Contactos en común", "Mi grafo"])

    with t[0]:
        estilo.seccion("Recibidas")
        if not recibidas:
            estilo.vacio("bandeja", "No tienes invitaciones pendientes")
        for i in recibidas:
            with st.container(border=True):
                c1, c2, c3, c4 = st.columns([4.2, 1.2, 1.2, 1.2])
                etiquetas = [("conexion", f"{i['en_comun']} contactos en común"), ("calendario", f"Enviada {i['fecha']}")]
                c1.markdown(estilo.tarjeta_persona(i["nombre"], i["titular"], '<div class="ox-meta">' + pills(etiquetas) + "</div>"),
                            unsafe_allow_html=True)
                with c2:
                    boton_ver_perfil(i["id"], f"r_vp_{i['id']}")
                if c3.button("Aceptar", key=f"r_ac_{i['id']}", type="primary", use_container_width=True):
                    ejecutar(us.aceptar_invitacion, yo, i["id"], exito="Ahora están conectados"); refrescar(); st.rerun()
                if c4.button("Ignorar", key=f"r_ig_{i['id']}", use_container_width=True):
                    ejecutar(us.rechazar_invitacion, yo, i["id"], exito="Invitación ignorada"); refrescar(); st.rerun()
        estilo.seccion("Enviadas")
        if not enviadas:
            st.caption("No tienes invitaciones enviadas pendientes.")
        for e in enviadas:
            with st.container(border=True):
                c1, c2, c3 = st.columns([4.8, 1.2, 1.2])
                c1.markdown(estilo.tarjeta_persona(e["nombre"], e["titular"],
                                                   '<div class="ox-meta">' + pills([("reloj", f"Enviada {e['fecha']}")], "warn") + "</div>", tam=40),
                            unsafe_allow_html=True)
                with c2:
                    boton_ver_perfil(e["id"], f"r_ve_{e['id']}")
                if c3.button("Cancelar", key=f"r_ca_{e['id']}", use_container_width=True):
                    ejecutar(us.cancelar_invitacion, yo, e["id"], exito="Invitación cancelada"); refrescar(); st.rerun()

    with t[1]:
        if not p["conexiones"]:
            estilo.vacio("brote", "Aún no tienes conexiones", "Ve a «Descubrir personas» para empezar a construir tu red.")
        filtro = st.text_input("Filtrar conexiones", placeholder="Nombre o titular…", key="r_filtro") if p["conexiones"] else ""
        lista = [c for c in p["conexiones"] if filtro.lower() in (c["nombre"] + (c["titular"] or "")).lower()]
        cols = st.columns(3)
        for k, c in enumerate(sorted(lista, key=lambda c: c["nombre"])):
            with cols[k % 3], st.container(border=True):
                estilo.html(estilo.tarjeta_persona(c["nombre"], c["titular"], tam=44))
                a, b = st.columns(2)
                with a:
                    boton_ver_perfil(c["id"], f"r_vc_{c['id']}")
                if b.button("Eliminar", icon=":material/person_remove:", key=f"r_del_{c['id']}", use_container_width=True):
                    st.session_state["confirmar_desconexion"] = c["id"]
                if st.session_state.get("confirmar_desconexion") == c["id"]:
                    st.warning("¿Eliminar esta conexión?")
                    x, y = st.columns(2)
                    if x.button("Sí, eliminar", key=f"r_si_{c['id']}", type="primary", use_container_width=True):
                        ejecutar(us.desconectar, yo, c["id"], exito="Conexión eliminada")
                        st.session_state.pop("confirmar_desconexion"); refrescar(); st.rerun()
                    if y.button("No", key=f"r_no_{c['id']}", use_container_width=True):
                        st.session_state.pop("confirmar_desconexion"); st.rerun()

    with t[2]:
        estilo.seccion("Sugerencias para ti")
        st.caption("Afinidad = 3 por cada contacto en común + 2 por cada habilidad compartida + 2 si trabajan en la misma empresa "
                   "+ 2 por cada proyecto compartido.")
        sugeridos = rec.recomendar_contactos(yo, 6)
        if not sugeridos:
            estilo.vacio("habilidad", "Aún no hay sugerencias", "Agrega habilidades o una empresa en Mi perfil para descubrir personas afines.")
        cols = st.columns(3)
        for k, r in enumerate(sugeridos):
            with cols[k % 3], st.container(border=True):
                estilo.html(estilo.tarjeta_persona(
                    r["nombre"], r["titular"], detalle_sugerencia(r),
                    f'<span class="ox-pill ind" style="font-weight:700" title="Puntaje de afinidad">Afinidad {r["puntaje"]}</span>'))
                _acciones(yo, r["id"], conectados, ids_env, ids_rec, f"r_sug_{r['id']}")
        estilo.seccion("Buscar en toda la red")
        texto = st.text_input("Buscar profesionales", placeholder="Nombre, titular o ciudad (ej.: React, Cali)", key="r_buscar")
        if texto.strip():
            res = [u for u in us.listar_usuarios(texto) if u["id"] != yo][:24]
            if not res:
                estilo.vacio("buscar", "Sin coincidencias", "Pruebe con otro término.")
            cols = st.columns(3)
            for k, u in enumerate(res):
                with cols[k % 3], st.container(border=True):
                    meta = [("ubicacion", u["ciudad"] or "—")] + ([("empresa", u["empresa_actual"])] if u["empresa_actual"] else [])
                    estilo.html(estilo.tarjeta_persona(u["nombre"], u["titular"], f'<div class="ox-meta">{pills(meta)}</div>', tam=42))
                    _acciones(yo, u["id"], conectados, ids_env, ids_rec, f"r_bus_{u['id']}")

    with t[3]:
        ops = {k: v for k, v in opciones_usuarios().items() if k != yo}
        otro = st.selectbox("Comparar mi red con", list(ops), format_func=lambda i: ops[i], key="r_cc")
        comunes = red.contactos_en_comun(yo, otro)
        grado = red.grado_separacion(yo, otro)["grado"]
        estilo.html(f'<div class="ox-s" style="margin:.4rem 0 .8rem">Tienen <b>{len(comunes)}</b> contacto(s) en común'
                    f'{" y ya están conectados" if otro in conectados else ""}. '
                    f'Grado de separación: <b>{grado if grado is not None else "sin camino"}</b></div>')
        boton_ver_perfil(otro, "r_cc_vp")
        cols = st.columns(3)
        for k, c in enumerate(comunes):
            with cols[k % 3], st.container(border=True):
                estilo.html(estilo.tarjeta_persona(c["nombre"], c["titular"], tam=40))
                boton_ver_perfil(c["id"], f"r_ccv_{c['id']}")

    with t[4]:
        saltos = st.radio("Profundidad", [1, 2], horizontal=True, format_func=lambda s: f"{s} salto(s)", key="r_saltos")
        leyenda()
        grafo(gv.ego("Usuario", yo, saltos), altura=600, resaltar={yo})
