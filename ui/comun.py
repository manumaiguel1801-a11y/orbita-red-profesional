"""Componentes y utilidades compartidas por las páginas (basados en ui/estilo.py)."""
from __future__ import annotations

import textwrap

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from neo4j.exceptions import ConstraintError, Neo4jError, ServiceUnavailable

from orbita import catalogo, usuarios
from orbita import grafo_visual as gv
from ui import estilo
from ui.estilo import esc, iniciales  # noqa: F401  (reexportados)

_CLASES = {"azul": "ind", "ok": "ok", "falta": "no", "": ""}


def aplicar_estilo() -> None:
    estilo.aplicar()


def cabecera(titulo: str, subtitulo: str = "", icono: str = "") -> None:
    estilo.encabezado(titulo, subtitulo, icono)


def kpi(col, valor, etiqueta: str, icono: str = "", color: str = "violeta") -> None:
    estilo.stat(col, valor, etiqueta, icono, color)


def chips(items, clase: str = "") -> str:
    return estilo.pills(items, _CLASES.get(clase, clase))


def tarjeta(titulo: str, subtitulo: str = "", cuerpo_html: str = "", puntaje=None) -> None:
    p = (f'<span class="ox-pill ind" style="float:right;font-weight:700">{esc(puntaje)}</span>' if puntaje is not None else "")
    st.markdown(f'<div class="ox-card">{p}<div class="ox-t">{esc(titulo)}</div><div class="ox-s">{esc(subtitulo)}</div>'
                f'<div class="ox-meta" style="display:block">{cuerpo_html}</div></div>', unsafe_allow_html=True)


def ver_cypher(*consultas: str, titulo: str = "Ver consulta Cypher utilizada") -> None:
    with st.expander(titulo, icon=":material/code:"):
        for q in consultas:
            st.code(textwrap.dedent(q).strip(), language="cypher")


def tabla(filas: list[dict], columnas: dict[str, str] | None = None, altura: int | None = None) -> None:
    if not filas:
        estilo.vacio("bandeja", "Sin resultados", "No hay datos para mostrar con estos criterios.")
        return
    df = pd.DataFrame(filas)
    for c in df.columns:
        if df[c].apply(lambda v: isinstance(v, list)).any():
            df[c] = df[c].apply(lambda v: ", ".join(map(str, v)) if isinstance(v, list) else v)
    if columnas:
        df = df[[c for c in columnas if c in df.columns]].rename(columns=columnas)
    st.dataframe(df, use_container_width=True, hide_index=True, height=altura)


def grafo(filas: list[dict], altura: int = 600, **kw) -> None:
    if not filas:
        estilo.vacio("red", "Nada que dibujar", "No hay nodos para estos filtros.")
        return
    components.html(gv.html(filas, altura=altura, **kw), height=altura + 20, scrolling=False)


def leyenda() -> None:
    st.markdown('<div class="ox-leyenda">' + "".join(
        f'<span><i style="background:{c};color:{c}"></i>{e}</span>' for e, c in gv.COLORES.items()) + "</div>",
        unsafe_allow_html=True)


def ruta_html(ruta: dict) -> str:
    partes = []
    for i, n in enumerate(ruta["nodos"]):
        partes.append(f'<span class="ox-paso" style="background:{gv.COLORES.get(n["etiqueta"], "#64748b")}">{esc(n["nombre"])}</span>')
        if i < len(ruta["relaciones"]):
            partes.append(f'<span class="ox-flecha">─[{esc(ruta["relaciones"][i])}]─</span>')
    return f'<div class="ox-ruta">{"".join(partes)}</div>'


# ---------------------------------------------------------------- Datos de selección (caché corta)
@st.cache_data(ttl=60, show_spinner=False)
def opciones_usuarios() -> dict[str, str]:
    return {u["id"]: f'{u["nombre"]} · {u["titular"] or ""}' for u in usuarios.listar_usuarios()}


@st.cache_data(ttl=60, show_spinner=False)
def opciones_empresas() -> dict[str, str]:
    return {e["id"]: e["nombre"] for e in catalogo.listar_empresas()}


@st.cache_data(ttl=60, show_spinner=False)
def opciones_proyectos() -> dict[str, str]:
    return {p["id"]: p["nombre"] for p in catalogo.listar_proyectos()}


@st.cache_data(ttl=60, show_spinner=False)
def opciones_ofertas(solo_activas: bool = False) -> dict[str, str]:
    return {o["id"]: f'{o["titulo"]} · {o["empresa"]}' + ("" if o["activa"] else " (cerrada)")
            for o in catalogo.listar_ofertas(solo_activas)}


@st.cache_data(ttl=60, show_spinner=False)
def opciones_habilidades() -> list[str]:
    return [h["nombre"] for h in catalogo.listar_habilidades()]


@st.cache_data(ttl=60, show_spinner=False)
def categorias_habilidad() -> list[str]:
    cats = sorted({h["categoria"] or "General" for h in catalogo.listar_habilidades()})
    return cats or ["General"]


def refrescar() -> None:
    """Invalida la caché tras una escritura para que la interfaz refleje Neo4j."""
    st.cache_data.clear()


def seleccionar(etiqueta: str, opciones: dict[str, str], key: str, indice: int = 0, **kw):
    if not opciones:
        st.warning("No hay registros disponibles.")
        return None
    ids = list(opciones)
    return st.selectbox(etiqueta, ids, index=min(indice, len(ids) - 1), format_func=lambda i: opciones.get(i, i), key=key, **kw)


def ejecutar(funcion, *args, exito: str | None = None, **kwargs):
    """Ejecuta una operación sobre Neo4j mostrando errores comprensibles en español."""
    try:
        r = funcion(*args, **kwargs)
        if exito:
            st.toast(exito, icon=":material/check_circle:")
        return r
    except ConstraintError:
        st.error("Ya existe un registro con ese valor único (por ejemplo, el mismo correo o nombre).")
    except PermissionError as e:
        st.error(f"{e}")
    except ValueError as e:
        msg = e.args[0] if e.args else str(e)
        st.error(" ".join(msg.values()) if isinstance(msg, dict) else str(msg))
    except ServiceUnavailable:
        st.error("No fue posible conectarse con Neo4j AuraDB. Verifique su conexión y el archivo .env.")
    except Neo4jError as e:
        st.error(f"Error de Neo4j: {e.message}")
    return None
