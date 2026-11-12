"""Órbita · Red Profesional — punto de entrada de Streamlit.

Ejecutar:  streamlit run app.py
"""
from pathlib import Path

import streamlit as st

st.set_page_config(page_title="Órbita · Red Profesional", page_icon=str(Path(__file__).resolve().parent / "assets" / "icono.svg"), layout="wide", initial_sidebar_state="expanded")

from orbita import usuarios as us  # noqa: E402
from orbita.db import ConfiguracionError, get_driver  # noqa: E402
from ui import (admin_pg, analitica_pg, auth_pg, catalogo_pg, empleos_pg, empresas_pg, estilo, explorador_pg,  # noqa: E402
                inicio, mi_red_pg, perfil_pg, reclutador_pg, recomendaciones_pg, red_pg, rutas, sesion, usuarios_pg)

estilo.aplicar()

try:
    get_driver()
except ConfiguracionError as e:
    st.error(f"{e}")
    st.stop()
except Exception as e:  # noqa: BLE001
    st.error("No fue posible conectarse con Neo4j AuraDB. Revise NEO4J_URI, NEO4J_USERNAME y NEO4J_PASSWORD en su archivo .env "
             "y que la instancia esté activa (las instancias Free se pausan tras días sin uso).")
    st.caption(type(e).__name__)
    st.stop()

sesion.sincronizar()
yo = sesion.usuario()

# ------------------------------------------------------------------ Visitante: solo acceso
if not yo:
    st.navigation([st.Page(auth_pg.pagina, title="Ingresar", icon=":material/login:", url_path="ingresar")], position="hidden").run()
    st.stop()

# ------------------------------------------------------------------ Usuario autenticado
P = rutas.PAGINAS
P["inicio"] = st.Page(inicio.pagina, title="Inicio", icon=":material/space_dashboard:", url_path="inicio", default=True)
P["perfil"] = st.Page(perfil_pg.pagina, title="Mi perfil", icon=":material/account_circle:", url_path="perfil")
invitaciones = len(us.invitaciones_recibidas(yo["id"]))
P["red"] = st.Page(mi_red_pg.pagina, title=f"Mi red{f' ({invitaciones})' if invitaciones else ''}", icon=":material/hub:", url_path="mi-red")
P["empleos"] = st.Page(empleos_pg.pagina, title="Empleos", icon=":material/work:", url_path="empleos")
P["proyectos"] = st.Page(catalogo_pg.pagina_proyectos, title="Proyectos", icon=":material/folder_open:", url_path="proyectos")

paginas = {"Mi espacio": [P["inicio"], P["perfil"], P["red"], P["empleos"], P["proyectos"]]}
if sesion.es_reclutador():
    P["empresa"] = st.Page(reclutador_pg.pagina, title="Mi empresa", icon=":material/target:", url_path="mi-empresa")
    paginas["Reclutamiento"] = [P["empresa"]]
paginas["Explorar el grafo"] = [
    st.Page(recomendaciones_pg.pagina, title="Recomendaciones", icon=":material/auto_awesome:", url_path="recomendaciones"),
    st.Page(red_pg.pagina, title="Rutas y conexiones", icon=":material/route:", url_path="rutas"),
    st.Page(analitica_pg.pagina, title="Analítica", icon=":material/monitoring:", url_path="analitica"),
    st.Page(explorador_pg.pagina, title="Explorador del grafo", icon=":material/scatter_plot:", url_path="grafo"),
]
if sesion.es_admin():
    paginas["Administración"] = [
        st.Page(usuarios_pg.pagina, title="Usuarios y cuentas", icon=":material/manage_accounts:", url_path="usuarios"),
        st.Page(empresas_pg.pagina, title="Empresas y ofertas", icon=":material/apartment:", url_path="empresas"),
        st.Page(catalogo_pg.pagina_habilidades, title="Habilidades", icon=":material/psychology:", url_path="habilidades"),
        st.Page(admin_pg.pagina, title="Base de datos", icon=":material/database:", url_path="admin"),
    ]

RAIZ = Path(__file__).resolve().parent
st.logo(str(RAIZ / "assets" / "logo.svg"), size="large", icon_image=str(RAIZ / "assets" / "icono.svg"))

pg = st.navigation(paginas)

if st.session_state.pop("ir_a_perfil", False):
    st.switch_page(P["perfil"])

with st.sidebar:
    st.write("")
    estilo.html(f'<div class="ox-me">{estilo.avatar(yo["nombre"], 38)}<div style="min-width:0"><div class="n">{estilo.esc(yo["nombre"])}</div>'
                f'{estilo.badge_rol(yo["rol"])}</div></div>')
    if st.button("Cerrar sesión", icon=":material/logout:", use_container_width=True, key="logout"):
        sesion.cerrar()
        st.rerun()
    estilo.html('<div style="font-size:.78rem;color:#71717A"><span class="ox-vivo"></span>Conectado a Neo4j AuraDB</div>')

pg.run()
