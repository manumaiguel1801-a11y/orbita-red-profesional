"""Panel de analítica: influencia, comunidades y habilidades más demandadas."""
import plotly.express as px
import streamlit as st

from orbita import analitica as an
from orbita import grafo_visual as gv
from ui import sesion
from ui.comun import cabecera, chips, ejecutar, grafo, tabla, tarjeta, ver_cypher


def pagina():
    cabecera("Panel de analítica", "Usuarios más influyentes, comunidades detectadas y habilidades más demandadas", "grafica")
    t = st.tabs(["Usuarios influyentes", "Comunidades", "Habilidades demandadas", "Empresas"])

    with t[0]:
        st.info("**Grado** (Cypher): número de conexiones. **PageRank** (d = 0.85): importancia según la importancia de los contactos. "
                "**Intermediación**: fracción de caminos más cortos que pasan por la persona (puentes entre grupos). "
                "**Índice de influencia** = promedio de las tres métricas normalizadas al máximo (0-100).", icon=":material/functions:")
        n = st.slider("Mostrar", 5, 43, 10, key="inf_n")
        filas = an.usuarios_influyentes(n)
        c1, c2 = st.columns([1.1, 1])
        with c1:
            fig = px.bar(filas[::-1], x="indice_influencia", y="nombre", orientation="h", color="intermediacion",
                         labels={"indice_influencia": "Índice de influencia", "nombre": "", "intermediacion": "Intermediación"})
            fig.update_layout(height=80 + 30 * len(filas), margin=dict(l=0, r=0, t=10, b=0))
            st.plotly_chart(fig, use_container_width=True)
        with c2:
            fig = px.scatter(filas, x="conexiones", y="pagerank", size="intermediacion", hover_name="nombre", text="nombre",
                             labels={"conexiones": "Conexiones (grado)", "pagerank": "PageRank"}, size_max=40)
            fig.update_traces(textposition="top center", textfont_size=9, marker=dict(color="#8B5CF6", opacity=.8, line=dict(color="#C4B5FD", width=1)))
            fig.update_layout(height=80 + 30 * len(filas), margin=dict(l=0, r=0, t=10, b=0))
            st.plotly_chart(fig, use_container_width=True)
        tabla(filas, {"nombre": "Profesional", "titular": "Titular", "empresa": "Empresa", "conexiones": "Conexiones",
                      "alcance_2_saltos": "Alcance 2 saltos", "pagerank": "PageRank", "intermediacion": "Intermediación",
                      "indice_influencia": "Índice"})
        ver_cypher(an.Q_CENTRALIDAD_GRADO, an.Q_ARISTAS_CONEXION)

    with t[1]:
        metodo = st.radio("Método de detección", ["louvain", "componentes"], horizontal=True,
                          format_func=lambda m: {"louvain": "Louvain (modularidad, semilla 42)", "componentes": "Componentes conectados"}[m])
        filas = an.comunidades(metodo)
        resumen = an.resumen_comunidades(filas)
        m = st.columns(3)
        m[0].metric("Comunidades detectadas", len(resumen))
        m[1].metric("Modularidad", an.modularidad(filas), help="> 0.3 suele indicar estructura de comunidades significativa")
        m[2].metric("Comunidad más grande", max((r["tamano"] for r in resumen), default=0))
        with st.expander("¿Cómo se calculan y qué limitaciones tienen?", icon=":material/info:"):
            st.markdown("""
- **AuraDB Free no incluye Graph Data Science (GDS)**, por eso el subgrafo `(:Usuario)-[:CONECTA_CON]-(:Usuario)` se extrae
  **en tiempo real** de Neo4j con Cypher y se procesa con NetworkX en el servidor de la aplicación.
- **Componentes conectados**: agrupa a quienes están unidos por algún camino. Es exacto, pero grueso: una red bien conectada
  queda en un solo componente.
- **Louvain**: optimiza la *modularidad* (más conexiones dentro del grupo que las esperadas al azar).
  Limitaciones: es heurístico (no garantiza el óptimo), depende de la semilla (se fija en 42 para que sea reproducible),
  tiene *límite de resolución* (puede fusionar grupos pequeños), solo usa `CONECTA_CON` sin pesos y se ejecuta en memoria,
  lo que no escala a millones de nodos (para eso se usaría GDS en AuraDS/Enterprise).
""")
        col_g, col_r = st.columns([1.3, 1])
        with col_g:
            aristas = gv.subgrafo(["Usuario"], ["CONECTA_CON"], 1000)
            # incluir usuarios aislados (sin aristas) como lazos invisibles no es posible en la tabla; se listan a la derecha
            grafo(aristas, altura=540, comunidades={f["id"]: f["comunidad"] for f in filas})
        with col_r:
            for r in resumen:
                color = gv.PALETA_COMUNIDADES[(r["comunidad"] - 1) % len(gv.PALETA_COMUNIDADES)]
                tarjeta(f'Comunidad {r["comunidad"]} · {r["tamano"]} miembros', f'{r["ciudad_predominante"] or "—"}',
                        f'<span style="display:inline-block;width:12px;height:12px;border-radius:3px;background:{color}"></span> '
                        + chips(r["habilidades_predominantes"], "azul") + "<br>" + chips(r["empresas_predominantes"], "ok")
                        + "<br><small>" + ", ".join(r["miembros"][:12]) + ("…" if len(r["miembros"]) > 12 else "") + "</small>")
        if sesion.es_admin() and st.button("Guardar comunidad como propiedad u.comunidad en Neo4j"):
            n = ejecutar(an.guardar_comunidades, filas, exito="Comunidades guardadas")
            if n:
                st.success(f"{n} usuarios actualizados (SET u.comunidad).")
        ver_cypher(an.Q_ARISTAS_CONEXION, an.Q_GUARDAR_COMUNIDAD)

    with t[2]:
        st.markdown("**¿Qué habilidades son las más demandadas en las ofertas?**")
        c1, c2 = st.columns([1, 1])
        solo = c1.toggle("Solo ofertas activas", True, key="dem_act")
        n = c2.slider("Top", 5, 37, 15, key="dem_n")
        dem = an.habilidades_demandadas(n, solo)
        if dem:
            fig = px.bar(dem, x="habilidad", y=["ofertas", "profesionales_que_la_tienen"], barmode="group",
                         labels={"value": "Cantidad", "habilidad": "", "variable": ""},
                         color_discrete_map={"ofertas": "#8B5CF6", "profesionales_que_la_tienen": "#A3E635"})
            fig.for_each_trace(lambda tr: tr.update(name={"ofertas": "Ofertas que la requieren (demanda)",
                                                          "profesionales_que_la_tienen": "Profesionales que la tienen (oferta)"}[tr.name]))
            fig.update_layout(height=420, margin=dict(l=0, r=0, t=10, b=0), legend=dict(orientation="h", y=1.1))
            st.plotly_chart(fig, use_container_width=True)
        tabla(dem, {"habilidad": "Habilidad", "categoria": "Categoría", "ofertas": "Ofertas", "obligatoria_en": "Obligatoria en",
                    "profesionales_que_la_tienen": "Profesionales", "proyectos_que_la_usan": "Proyectos"})
        ver_cypher(an.Q_HABILIDADES_DEMANDADAS)
        cat = an.demanda_por_categoria()
        if cat:
            fig = px.pie(cat, names="categoria", values="requerimientos", hole=.55)
            fig.update_layout(height=340, margin=dict(l=0, r=0, t=30, b=0), title="Demanda por categoría")
            st.plotly_chart(fig, use_container_width=True)
            ver_cypher(an.Q_DEMANDA_POR_CATEGORIA)

    with t[3]:
        emp = an.empresas_activas()
        fig = px.bar(emp, x="empresa", y=["ofertas", "postulaciones", "empleados"], barmode="group",
                     labels={"value": "Cantidad", "empresa": "", "variable": ""}, color_discrete_sequence=["#8B5CF6", "#A3E635", "#22D3EE"])
        fig.update_layout(height=380, margin=dict(l=0, r=0, t=10, b=0), legend=dict(orientation="h", y=1.1))
        st.plotly_chart(fig, use_container_width=True)
        tabla(emp)
        ver_cypher(an.Q_EMPRESAS_ACTIVAS)
        ciudades = an.usuarios_por_ciudad()
        fig = px.pie(ciudades, names="ciudad", values="usuarios", hole=.5, title="Profesionales por ciudad")
        fig.update_layout(height=320, margin=dict(l=0, r=0, t=40, b=0))
        st.plotly_chart(fig, use_container_width=True)
