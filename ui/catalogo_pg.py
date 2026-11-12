"""Habilidades y proyectos (CRUD, tecnologías, miembros, proyectos relacionados)."""
import streamlit as st

from orbita import catalogo as cat
from orbita import recomendaciones as rec
from orbita import red
from orbita import usuarios as us
from ui import sesion
from ui.comun import (cabecera, categorias_habilidad, chips, ejecutar, opciones_habilidades, opciones_proyectos,
                      opciones_usuarios, refrescar, tabla, tarjeta, ver_cypher)

ESTADOS_PROY = ["Propuesta", "En curso", "Finalizado"]


def pagina_habilidades():
    cabecera("Habilidades", "Catálogo de competencias, quién las tiene, qué ofertas las piden y qué proyectos las usan", "habilidad")
    t = st.tabs(["Catálogo", "Crear / editar / eliminar", "Buscar profesionales por habilidades"])
    with t[0]:
        habs = cat.listar_habilidades()
        tabla(habs, {"nombre": "Habilidad", "categoria": "Categoría", "usuarios": "Profesionales",
                     "ofertas": "Ofertas que la requieren", "proyectos": "Proyectos que la usan"}, altura=520)
        ver_cypher(cat.Q_LISTAR_HABILIDADES)
    with t[1]:
        a, b = st.columns(2)
        with a, st.form("crear_hab", clear_on_submit=True):
            st.markdown("**Nueva habilidad**")
            n = st.text_input("Nombre *")
            c = st.selectbox("Categoría", categorias_habilidad() + ["General"])
            if st.form_submit_button("Crear", type="primary") and n:
                if ejecutar(cat.crear_habilidad, n, c, exito="Habilidad creada"):
                    refrescar()
        with b:
            st.markdown("**Editar / eliminar**")
            h = st.selectbox("Habilidad", opciones_habilidades(), key="ed_hab")
            if h:
                actual = next(x for x in cat.listar_habilidades() if x["nombre"] == h)
                with st.form(f"ed_hab_{h}"):
                    nn = st.text_input("Nombre", h)
                    cats = categorias_habilidad()
                    cc = st.selectbox("Categoría", cats, index=cats.index(actual["categoria"]) if actual["categoria"] in cats else 0)
                    if st.form_submit_button("Guardar"):
                        if ejecutar(cat.actualizar_habilidad, h, nn, cc, exito="Habilidad actualizada"):
                            refrescar(); st.rerun()
                total = actual["usuarios"] + actual["ofertas"] + actual["proyectos"]
                conf = st.checkbox(f"Confirmo eliminarla (afecta {total} relaciones)", key=f"del_hab_{h}")
                if st.button("Eliminar habilidad", disabled=not conf, key=f"btn_del_hab_{h}"):
                    ejecutar(cat.eliminar_habilidad, h, exito="Habilidad eliminada"); refrescar(); st.rerun()
        ver_cypher(cat.Q_CREAR_HABILIDAD, cat.Q_ACTUALIZAR_HABILIDAD, cat.Q_ELIMINAR_HABILIDAD)
    with t[2]:
        sel = st.multiselect("Habilidades buscadas", opciones_habilidades(), default=["Python", "SQL"] if "Python" in opciones_habilidades() else None)
        if sel:
            tabla(red.usuarios_con_habilidades(sel), {"nombre": "Profesional", "titular": "Titular", "tiene": "Habilidades que posee",
                                                       "coincidencias": "Coincidencias", "nivel_promedio": "Nivel promedio"})
            ver_cypher(red.Q_USUARIOS_CON_HABILIDAD)


def pagina_proyectos():
    cabecera("Proyectos", "Iniciativas, sus tecnologías (USA_TECNOLOGIA) y sus miembros (PARTICIPA_EN)", "proyecto")
    admin = sesion.es_admin()
    nombres = ["Proyectos", "Proyectos relacionados", "Colaboradores sugeridos"]
    if admin:
        nombres += ["Crear / editar / eliminar", "Tecnologías y miembros"]
    tabs = st.tabs(nombres)
    t = {0: tabs[0], 3: tabs[1], 4: tabs[2]}
    if admin:
        _proyectos_admin(tabs[3], tabs[4])
    else:
        st.caption("Para crear un proyecto o unirse a uno, vaya a Mi perfil → Proyectos.")
    with t[0]:
        for p in cat.listar_proyectos():
            tarjeta(p["nombre"], f'{p["estado"]} · {p["anio"]} · {p["descripcion"] or ""}',
                    "Tecnologías: " + chips(p["tecnologias"], "azul") + "<br>Miembros: " + chips(p["miembros"]))
        ver_cypher(cat.Q_LISTAR_PROYECTOS)
    with t[3]:
        st.markdown("**¿Qué proyectos comparten tecnologías o miembros relacionados?**")
        st.caption("Puntaje = 2·tecnologías compartidas + 3·miembros compartidos + 1·pares de miembros conectados entre sí (CONECTA_CON).")
        ops = opciones_proyectos()
        pid = st.selectbox("Proyecto de referencia", list(ops), format_func=lambda i: ops[i], key="rel_proy", index=min(9, len(ops) - 1)) if ops else None
        if pid:
            for r in rec.proyectos_relacionados(pid):
                tarjeta(r["proyecto"], f'{len(r["tecnologias_compartidas"])} tecnologías · {len(r["miembros_compartidos"])} miembros compartidos · '
                                       f'{len(r["miembros_relacionados"])} pares conectados',
                        "Tecnologías: " + chips(r["tecnologias_compartidas"], "azul")
                        + "<br>Miembros compartidos: " + chips(r["miembros_compartidos"], "ok")
                        + "<br>Miembros relacionados: " + chips(r["miembros_relacionados"][:8]), puntaje=r["puntaje"])
            ver_cypher(rec.Q_PROYECTOS_RELACIONADOS)
        st.markdown("**Ranking global de pares de proyectos relacionados**")
        tabla(rec.pares_proyectos_relacionados(15), {"proyecto_a": "Proyecto A", "proyecto_b": "Proyecto B",
                                                     "tecnologias_compartidas": "Tecnologías compartidas",
                                                     "miembros_compartidos": "Miembros compartidos",
                                                     "pares_conectados": "Pares de miembros conectados", "puntaje": "Puntaje"})
        ver_cypher(rec.Q_PARES_PROYECTOS)
    with t[4]:
        st.caption("Puntaje = 2·tecnologías del proyecto que domina + 1.5·miembros del proyecto con los que ya está conectado.")
        ops = opciones_proyectos()
        pid = st.selectbox("Proyecto", list(ops), format_func=lambda i: ops[i], key="col_proy") if ops else None
        if pid:
            for c in rec.colaboradores_para_proyecto(pid):
                tarjeta(c["nombre"], c["titular"], "Domina: " + chips(c["tecnologias"], "ok")
                        + f' · nivel promedio {c["nivel_promedio"]}<br>Conoce a: ' + chips(c["miembros_conocidos"]), puntaje=c["puntaje"])
            ver_cypher(rec.Q_RECOMENDAR_COLABORADORES_PROYECTO)



def _proyectos_admin(t1, t2):
    """Pestañas de gestión total de proyectos (solo administrador)."""
    with t1:
        a, b = st.columns(2)
        with a, st.form("crear_proy", clear_on_submit=True):
            st.markdown("**Nuevo proyecto**")
            datos = {"nombre": st.text_input("Nombre *"), "descripcion": st.text_area("Descripción", height=70),
                     "estado": st.selectbox("Estado", ESTADOS_PROY), "anio": st.number_input("Año", 2000, 2100, 2025)}
            tecs = st.multiselect("Tecnologías", opciones_habilidades())
            if st.form_submit_button("Crear proyecto", type="primary"):
                p = ejecutar(cat.crear_proyecto, datos, tecs, exito="Proyecto creado")
                if p:
                    refrescar(); st.success(f'Proyecto `{p["id"]}` creado.')
        with b:
            st.markdown("**Editar / eliminar**")
            ops = opciones_proyectos()
            pid = st.selectbox("Proyecto", list(ops), format_func=lambda i: ops[i], key="ed_proy") if ops else None
            if pid:
                p = next(x for x in cat.listar_proyectos() if x["id"] == pid)
                with st.form(f"ed_proy_{pid}"):
                    datos = {"nombre": st.text_input("Nombre", p["nombre"]), "descripcion": st.text_area("Descripción", p["descripcion"] or "", height=70),
                             "estado": st.selectbox("Estado", ESTADOS_PROY, index=ESTADOS_PROY.index(p["estado"]) if p["estado"] in ESTADOS_PROY else 0),
                             "anio": st.number_input("Año", 2000, 2100, int(p["anio"] or 2025))}
                    if st.form_submit_button("Guardar"):
                        if ejecutar(cat.actualizar_proyecto, pid, datos, exito="Proyecto actualizado"):
                            refrescar(); st.rerun()
                conf = st.checkbox("Confirmo eliminar este proyecto", key=f"del_proy_{pid}")
                if st.button("Eliminar proyecto", disabled=not conf, key=f"btn_del_proy_{pid}"):
                    ejecutar(cat.eliminar_proyecto, pid, exito="Proyecto eliminado"); refrescar(); st.rerun()
        ver_cypher(cat.Q_CREAR_PROYECTO, cat.Q_ACTUALIZAR_PROYECTO, cat.Q_ELIMINAR_PROYECTO)
    with t2:
        ops = opciones_proyectos()
        pid = st.selectbox("Proyecto", list(ops), format_func=lambda i: ops[i], key="tm_proy") if ops else None
        if pid:
            p = next(x for x in cat.listar_proyectos() if x["id"] == pid)
            a, b = st.columns(2)
            with a:
                st.markdown("**Tecnologías** " + chips(p["tecnologias"], "azul"), unsafe_allow_html=True)
                h = st.selectbox("Tecnología", opciones_habilidades(), key="tm_h")
                c1, c2 = st.columns(2)
                if c1.button("Agregar tecnología", type="primary"):
                    ejecutar(cat.agregar_tecnologia, pid, h, exito="Tecnología agregada"); refrescar(); st.rerun()
                if c2.button("Quitar tecnología") and h in p["tecnologias"]:
                    ejecutar(cat.quitar_tecnologia, pid, h, exito="Tecnología retirada"); refrescar(); st.rerun()
                ver_cypher(cat.Q_AGREGAR_TECNOLOGIA, cat.Q_QUITAR_TECNOLOGIA)
            with b:
                st.markdown("**Miembros** " + chips(p["miembros"]), unsafe_allow_html=True)
                uo = opciones_usuarios()
                uid = st.selectbox("Profesional", list(uo), format_func=lambda i: uo[i], key="tm_u")
                rol = st.text_input("Rol", "Colaborador", key="tm_rol")
                c1, c2 = st.columns(2)
                if c1.button("Agregar miembro", type="primary"):
                    ejecutar(us.vincular_proyecto, uid, pid, rol, exito="Miembro agregado"); refrescar(); st.rerun()
                if c2.button("Retirar miembro"):
                    ejecutar(us.desvincular_proyecto, uid, pid, exito="Miembro retirado"); refrescar(); st.rerun()
                ver_cypher(us.Q_VINCULAR_PROYECTO)
