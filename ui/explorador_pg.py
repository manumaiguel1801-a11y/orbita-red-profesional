"""Visualización interactiva del grafo."""
import streamlit as st

from orbita import grafo_visual as gv
from orbita import red
from ui import sesion
from ui.comun import (cabecera, grafo, leyenda, opciones_empresas, opciones_habilidades, opciones_ofertas,
                      opciones_proyectos, opciones_usuarios, ver_cypher)


def pagina():
    cabecera("Explorador del grafo", "Visualización interactiva: arrastre nodos, haga zoom y pase el cursor para ver detalles", "red")
    modo = st.radio("Vista", ["Vecindario de un nodo", "Subgrafo por tipos"], horizontal=True)
    leyenda()
    if modo == "Vecindario de un nodo":
        c1, c2, c3 = st.columns([1, 2, 1])
        etiqueta = c1.selectbox("Tipo de nodo", list(gv.COLORES))
        ops = {"Usuario": opciones_usuarios, "Empresa": opciones_empresas, "Oferta": lambda: opciones_ofertas(False),
               "Proyecto": opciones_proyectos, "Habilidad": lambda: {h: h for h in opciones_habilidades()}}[etiqueta]()
        claves = list(ops)
        yo = sesion.uid()
        clave = c2.selectbox("Nodo central", claves, format_func=lambda i: ops[i], key=f"exp_{etiqueta}",
                             index=claves.index(yo) if etiqueta == "Usuario" and yo in claves else 0)
        saltos = c3.radio("Profundidad", [1, 2], horizontal=True)
        filas = gv.ego(etiqueta, clave, saltos)
        st.caption(f"{len(filas)} relaciones dibujadas")
        grafo(filas, altura=640, resaltar={clave})
        ver_cypher(gv.Q_EGO % {"clave": "nombre" if etiqueta == "Habilidad" else "id", "saltos": saltos,
                               "na": "a {...}", "nb": "b {...}"})
    else:
        c1, c2, c3 = st.columns([2, 2, 1])
        etiquetas = c1.multiselect("Tipos de nodo", list(gv.COLORES), default=["Usuario", "Empresa", "Oferta"])
        tipos = c2.multiselect("Tipos de relación", red.TIPOS_RELACION, default=["CONECTA_CON", "TRABAJA_EN", "PUBLICA", "POSTULA_A"])
        limite = c3.number_input("Máx. relaciones", 50, 1500, 400, step=50)
        if etiquetas and tipos:
            filas = gv.subgrafo(etiquetas, tipos, limite)
            st.caption(f"{len(filas)} relaciones dibujadas")
            grafo(filas, altura=680)
        ver_cypher(gv.Q_SUBGRAFO)
