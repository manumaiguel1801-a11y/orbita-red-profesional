"""Registro de páginas (lo llena app.py) para poder enlazarlas con st.page_link / st.switch_page."""
import streamlit as st

PAGINAS: dict = {}


def enlace(clave: str, etiqueta: str, icono: str | None = None) -> None:
    if clave in PAGINAS:
        st.page_link(PAGINAS[clave], label=etiqueta, icon=icono)


def ir(clave: str) -> None:
    if clave in PAGINAS:
        st.switch_page(PAGINAS[clave])
