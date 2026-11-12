"""Administración: estado de la base, esquema y datos de demostración (con salvaguardas)."""
import streamlit as st

from orbita import datos_demo, esquema
from ui.comun import cabecera, ejecutar, refrescar, tabla, ver_cypher


def pagina():
    cabecera("Administración", "Estado de la base de datos Neo4j, restricciones y datos de demostración", "ajustes")
    nodos, rels = esquema.conteo_nodos(), esquema.conteo_relaciones()
    a, b = st.columns(2)
    with a:
        st.markdown("**Nodos por etiqueta**")
        tabla([{"Etiqueta": k, "Total": v} for k, v in nodos.items()])
    with b:
        st.markdown("**Relaciones por tipo**")
        tabla([{"Tipo": k, "Total": v} for k, v in rels.items()])
    ver_cypher(esquema.Q_CONTEO_NODOS, esquema.Q_CONTEO_RELACIONES)

    st.markdown("**Restricciones de unicidad**")
    tabla(esquema.listar_restricciones())
    if st.button("Crear / verificar restricciones e índices"):
        if ejecutar(esquema.crear_esquema, exito="Esquema verificado"):
            st.rerun()
    ver_cypher(*esquema.RESTRICCIONES, *esquema.INDICES)

    st.divider()
    st.markdown("### Datos de demostración")
    st.caption("La carga usa MERGE: no duplica registros ni borra nada. Restaura los datos de ejemplo que se hayan modificado.")
    if st.button("Cargar / completar datos de demostración"):
        r = ejecutar(datos_demo.cargar, exito="Datos de demostración cargados")
        if r:
            refrescar(); st.success(r); st.rerun()

    st.markdown("**Origen de los datos**")
    st.caption("Los nodos de demostración llevan la propiedad `demo`; los creados desde la aplicación no.")
    tabla(esquema.origen_datos(), {"etiqueta": "Etiqueta", "demo": "De demostración", "reales": "Creados por usuarios"})
    ver_cypher(esquema.Q_ORIGEN_DATOS)

    with st.expander("Eliminar solo los datos de demostración", icon=":material/science:"):
        st.info("Borra usuarios, empresas, proyectos, ofertas y habilidades ficticios. **Conserva** todo lo creado por usuarios reales; "
                "las habilidades y empresas de demostración que ya usan sus usuarios reales se conservan y pasan a ser datos permanentes.")
        txt = st.text_input("Escriba BORRAR DEMO para confirmar", key="borrar_demo_txt")
        if st.button("Eliminar datos de demostración", type="primary", disabled=txt != "BORRAR DEMO"):
            r = ejecutar(esquema.borrar_datos_demo, txt, exito="Datos de demostración eliminados")
            if r:
                refrescar(); st.success(f"Eliminados {r['eliminados']} nodos; conservados {r['conservados']} por estar en uso."); st.rerun()
    ver_cypher(esquema.Q_BORRAR_DEMO, esquema.Q_CONSERVAR_RESTANTES, titulo="Ver consultas de borrado de datos de demostración")

    with st.expander("Zona peligrosa: vaciar la base de datos", icon=":material/warning:"):
        total = sum(nodos.values())
        st.warning(f"Esta acción eliminará **{total} nodos** y **{sum(rels.values())} relaciones** de forma permanente, "
                   "**incluida su cuenta de administrador** (deberá recrearla con `python scripts/crear_admin.py`). "
                   "La aplicación nunca lo hace automáticamente.")
        texto = st.text_input("Escriba BORRAR para confirmar", key="borrar_txt")
        recargar = st.checkbox("Volver a cargar los datos de demostración después de vaciar", True)
        if st.button("Vaciar base de datos", type="primary", disabled=texto != "BORRAR"):
            if ejecutar(esquema.borrar_todo, texto, exito="Base vaciada"):
                if recargar:
                    datos_demo.cargar()
                refrescar(); st.rerun()
