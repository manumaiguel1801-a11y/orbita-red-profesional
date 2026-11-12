"""Gestión de la sesión en Streamlit.

El usuario autenticado vive en st.session_state["usuario"]. El token de sesión se guarda también
en la URL (?s=...) para sobrevivir a recargas de página; en Neo4j solo se almacena su hash.
En cada ejecución se revalida contra Neo4j: si un administrador desactiva la cuenta o cambia el rol,
el cambio se aplica de inmediato.
"""
from __future__ import annotations

import streamlit as st

from orbita import seguridad


def usuario() -> dict | None:
    return st.session_state.get("usuario")


def uid() -> str | None:
    u = usuario()
    return u["id"] if u else None


def rol() -> str:
    u = usuario()
    return u["rol"] if u else ""


def es_admin() -> bool:
    return rol() == "admin"


def es_reclutador() -> bool:
    return rol() in ("reclutador", "admin")


def iniciar(u: dict, token: str) -> None:
    st.session_state["usuario"] = u
    st.session_state["token"] = token
    st.query_params["s"] = token


def cerrar() -> None:
    u = usuario()
    if u:
        try:
            seguridad.cerrar_sesion(u["id"])
        except Exception:  # noqa: BLE001  (cerrar localmente aunque falle la red)
            pass
    for k in list(st.session_state.keys()):
        del st.session_state[k]
    st.query_params.clear()


def sincronizar() -> None:
    """Restaura la sesión desde la URL y la revalida en Neo4j en cada ejecución."""
    token = st.session_state.get("token") or st.query_params.get("s")
    if not token:
        return  # sin token: sesión inyectada (pruebas) o anónima
    u = seguridad.validar_sesion(token)
    if u is None:
        if usuario():
            st.session_state["aviso_sesion"] = "Su sesión expiró o fue cerrada. Inicie sesión de nuevo."
        for k in ("usuario", "token"):
            st.session_state.pop(k, None)
        st.query_params.clear()
        return
    st.session_state["usuario"] = u
    st.session_state["token"] = token
    if st.query_params.get("s") != token:
        st.query_params["s"] = token


def exigir(*roles: str) -> bool:
    """Muestra un aviso y devuelve False si el usuario no tiene alguno de los roles."""
    if rol() in roles:
        return True
    st.error("No tiene permisos para ver esta sección.")
    return False
