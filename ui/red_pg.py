"""Contactos en común, rutas más cortas y grado de separación."""
import streamlit as st

from orbita import grafo_visual as gv
from orbita import red
from ui import sesion
from ui.comun import (cabecera, ejecutar, grafo, leyenda, opciones_empresas, opciones_habilidades, opciones_ofertas,
                      opciones_proyectos, opciones_usuarios, ruta_html, tabla, ver_cypher)


def _opciones(etiqueta: str) -> dict:
    return {"Usuario": opciones_usuarios, "Empresa": opciones_empresas, "Oferta": lambda: opciones_ofertas(False),
            "Proyecto": opciones_proyectos, "Habilidad": lambda: {h: h for h in opciones_habilidades()}}[etiqueta]()


def pagina():
    cabecera("Red y rutas", "Contactos en común, caminos más cortos entre profesionales, empresas y oportunidades", "brujula")
    t = st.tabs(["Contactos en común", "Ruta más corta", "Grado de separación"])
    uo = opciones_usuarios()
    ids = list(uo)
    yo = sesion.uid()
    i_yo = ids.index(yo) if yo in ids else 0

    with t[0]:
        st.markdown("**¿Qué contactos en común existen entre dos profesionales?**")
        a, b = st.columns(2)
        ua = a.selectbox("Profesional A", ids, format_func=lambda i: uo[i], key="cc_a", index=i_yo)
        ub = b.selectbox("Profesional B", ids, format_func=lambda i: uo[i], key="cc_b", index=min(8, len(ids) - 1))
        if ua == ub:
            st.warning("Seleccione dos profesionales distintos.")
        else:
            comunes = red.contactos_en_comun(ua, ub)
            conectados = red.estan_conectados(ua, ub)
            m = st.columns(2)
            m[0].metric("Contactos en común", len(comunes))
            m[1].metric("¿Conectados directamente?", "Sí" if conectados else "No")
            tabla(comunes, {"nombre": "Contacto en común", "titular": "Titular", "ciudad": "Ciudad", "conexiones": "Conexiones totales"})
            ver_cypher(red.Q_CONTACTOS_EN_COMUN)

    with t[1]:
        st.markdown("**¿Cuál es la ruta más corta entre un usuario y una empresa (u otra entidad)?**")
        c1, c2 = st.columns(2)
        eo = c1.selectbox("Tipo de origen", list(gv.COLORES), index=0, key="r_eo")
        ed = c2.selectbox("Tipo de destino", list(gv.COLORES), index=1, key="r_ed")
        oo, od = _opciones(eo), _opciones(ed)
        origen = c1.selectbox("Origen", list(oo), format_func=lambda i: oo[i], key=f"r_o_{eo}",
                              index=i_yo if eo == "Usuario" else min(7, len(oo) - 1))
        destino = c2.selectbox("Destino", list(od), format_func=lambda i: od[i], key=f"r_d_{ed}", index=min(7, len(od) - 1))
        c3, c4, c5 = st.columns([2, 1, 1])
        modo = c3.selectbox("Relaciones permitidas", list(red.MODOS_RUTA), key="r_modo",
                            help="Red profesional: solo CONECTA_CON, TRABAJA_EN y PUBLICA (cómo llegar a través de personas).")
        max_s = c4.slider("Máx. saltos", 2, 12, 8, key="r_max")
        todas = c5.toggle("Todas las rutas mínimas", False, key="r_todas", help="allShortestPaths en lugar de shortestPath")
        rutas = ejecutar(red.ruta_mas_corta, eo, origen, ed, destino, red.MODOS_RUTA[modo], max_s, todas)
        if rutas is not None:
            if not rutas:
                st.warning("No existe una ruta con esas relaciones y ese número máximo de saltos (los nodos están en componentes distintos).")
            else:
                st.success(f"{len(rutas)} ruta(s) de longitud **{rutas[0]['saltos']}** saltos.")
                for r in rutas[:10]:
                    st.markdown(ruta_html(r), unsafe_allow_html=True)
                filas = [f for r in rutas for f in gv.filas_desde_ruta(r)]
                vistos, unicas = set(), []
                for f in filas:
                    k = (f["a"]["id"], f["tipo"], f["b"]["id"])
                    if k not in vistos:
                        vistos.add(k); unicas.append(f)
                leyenda()
                grafo(unicas, altura=420, resaltar={origen, destino})
        ver_cypher(red.construir_consulta_ruta(eo, ed, red.MODOS_RUTA[modo], max_s, todas))

    with t[2]:
        st.markdown("**Grado de separación** (solo a través de conexiones profesionales `CONECTA_CON`)")
        a, b = st.columns(2)
        ga = a.selectbox("Profesional A", ids, format_func=lambda i: uo[i], key="g_a", index=i_yo)
        gb = b.selectbox("Profesional B", ids, format_func=lambda i: uo[i], key="g_b", index=min(31, len(ids) - 1))
        if ga != gb:
            r = red.grado_separacion(ga, gb)
            if r["grado"] is None:
                st.warning("No están conectados por ningún camino: pertenecen a componentes distintos de la red.")
            else:
                st.metric("Grado de separación", r["grado"])
                st.markdown(" → ".join(f"**{n}**" for n in r["ruta"]))
        ver_cypher(red.Q_GRADO_SEPARACION)
