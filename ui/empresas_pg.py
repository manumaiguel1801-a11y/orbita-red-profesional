"""Empresas, ofertas laborales (con habilidades requeridas) y postulaciones."""
import streamlit as st

from orbita import catalogo as cat
from orbita import usuarios as us
from ui.estilo import pesos
from ui.comun import (cabecera, chips, ejecutar, opciones_empresas, opciones_habilidades, opciones_ofertas,
                      opciones_usuarios, refrescar, tabla, tarjeta, ver_cypher)

TAMANOS = ["Startup", "Pequeña", "Mediana", "Grande"]
MODALIDADES = ["Presencial", "Híbrido", "Remoto"]
NIVELES = ["Practicante", "Junior", "Semi Senior", "Senior", "Líder"]
ESTADOS = ["Enviada", "En revisión", "Entrevista", "Oferta", "Rechazada"]


def _sel(label, opciones: dict, key):
    if not opciones:
        st.info("No hay registros.")
        return None
    return st.selectbox(label, list(opciones), format_func=lambda i: opciones[i], key=key)


def pagina():
    cabecera("Empresas y ofertas", "Registrar empresas, publicar vacantes con sus habilidades requeridas y gestionar postulaciones", "empresa")
    t = st.tabs(["Empresas", "Ofertas", "Publicar oferta", "Requisitos de oferta", "Postulaciones"])

    # ------------------------------------------------------------ Empresas
    with t[0]:
        empresas = cat.listar_empresas()
        tabla(empresas, {"id": "ID", "nombre": "Empresa", "sector": "Sector", "ciudad": "Ciudad", "tamano": "Tamaño",
                         "empleados": "Empleados actuales", "ofertas": "Ofertas"})
        ver_cypher(cat.Q_LISTAR_EMPRESAS)
        a, b = st.columns(2)
        with a, st.form("crear_empresa", clear_on_submit=True):
            st.markdown("**Registrar empresa**")
            datos = {"nombre": st.text_input("Nombre *"), "sector": st.text_input("Sector"),
                     "ciudad": st.text_input("Ciudad"), "tamano": st.selectbox("Tamaño", TAMANOS),
                     "sitio_web": st.text_input("Sitio web"), "descripcion": st.text_area("Descripción", height=70)}
            if st.form_submit_button("Registrar empresa", type="primary"):
                e = ejecutar(cat.crear_empresa, datos, exito="Empresa registrada")
                if e:
                    refrescar(); st.success(f'Empresa **{e["nombre"]}** creada con id `{e["id"]}`.')
        with b:
            st.markdown("**Editar / eliminar empresa**")
            eid = _sel("Empresa", opciones_empresas(), "ed_emp")
            if eid:
                e = next(x for x in empresas if x["id"] == eid)
                with st.form(f"ed_emp_{eid}"):
                    datos = {"nombre": st.text_input("Nombre", e["nombre"]), "sector": st.text_input("Sector", e["sector"] or ""),
                             "ciudad": st.text_input("Ciudad", e["ciudad"] or ""),
                             "tamano": st.selectbox("Tamaño", TAMANOS, index=TAMANOS.index(e["tamano"]) if e["tamano"] in TAMANOS else 0),
                             "sitio_web": st.text_input("Sitio web", e["sitio_web"] or "")}
                    if st.form_submit_button("Guardar cambios"):
                        if ejecutar(cat.actualizar_empresa, eid, datos, exito="Empresa actualizada"):
                            refrescar(); st.rerun()
                conf = st.checkbox(f"Confirmo eliminar la empresa y sus {e['ofertas']} ofertas", key=f"del_emp_{eid}")
                if st.button("Eliminar empresa", disabled=not conf, key=f"btn_del_emp_{eid}"):
                    n = ejecutar(cat.eliminar_empresa, eid, exito="Empresa eliminada")
                    if n is not None:
                        refrescar(); st.success(f"Empresa eliminada junto con {n} ofertas."); st.rerun()
        ver_cypher(cat.Q_CREAR_EMPRESA, cat.Q_ACTUALIZAR_EMPRESA, cat.Q_ELIMINAR_EMPRESA, titulo="Ver consultas de escritura")

    # ------------------------------------------------------------ Ofertas
    with t[1]:
        c1, c2 = st.columns([1, 2])
        solo = c1.toggle("Solo ofertas activas", True)
        emp = c2.selectbox("Empresa", [""] + list(opciones_empresas()), format_func=lambda i: opciones_empresas().get(i, "Todas"))
        ofertas = cat.listar_ofertas(solo, emp)
        st.caption(f"{len(ofertas)} ofertas")
        for o in ofertas:
            req = [f'{r["habilidad"]} ≥{r["nivel_minimo"]}' + ("" if r["obligatoria"] else " (deseable)") for r in o["requisitos"]]
            meta = [o["empresa"], o["ciudad"], o["modalidad"], o["nivel"], pesos(o["salario"]), f'publicada {o["fecha_publicacion"]}']
            tarjeta(o["titulo"], " · ".join(str(m) for m in meta if m) + ("" if o["activa"] else " · CERRADA"),
                    "Requiere: " + chips(req, "azul"), puntaje=f'{o["postulantes"]} postulantes')
        ver_cypher(cat.Q_LISTAR_OFERTAS)

        st.markdown("**Editar / cerrar / eliminar oferta**")
        oid = _sel("Oferta", opciones_ofertas(False), "ed_of")
        if oid:
            o = next((x for x in cat.listar_ofertas(False) if x["id"] == oid), None)
            with st.form(f"ed_of_{oid}"):
                a, b, c = st.columns(3)
                datos = {"titulo": a.text_input("Título", o["titulo"]), "ciudad": b.text_input("Ciudad", o["ciudad"] or ""),
                         "modalidad": c.selectbox("Modalidad", MODALIDADES, index=MODALIDADES.index(o["modalidad"]) if o["modalidad"] in MODALIDADES else 0),
                         "nivel": a.selectbox("Nivel", NIVELES, index=NIVELES.index(o["nivel"]) if o["nivel"] in NIVELES else 1),
                         "salario": b.number_input("Salario (COP)", 0, 100_000_000, int(o["salario"] or 0), step=500_000),
                         "activa": c.toggle("Oferta activa", bool(o["activa"]))}
                if st.form_submit_button("Guardar"):
                    if ejecutar(cat.actualizar_oferta, oid, datos, exito="Oferta actualizada"):
                        refrescar(); st.rerun()
            conf = st.checkbox("Confirmo eliminar esta oferta y sus postulaciones", key=f"del_of_{oid}")
            if st.button("Eliminar oferta", disabled=not conf, key=f"btn_del_of_{oid}"):
                ejecutar(cat.eliminar_oferta, oid, exito="Oferta eliminada"); refrescar(); st.rerun()
            ver_cypher(cat.Q_ACTUALIZAR_OFERTA, cat.Q_ELIMINAR_OFERTA, titulo="Ver consultas de escritura")

    # ------------------------------------------------------------ Publicar
    with t[2]:
        eid = _sel("Empresa que publica", opciones_empresas(), "pub_emp")
        a, b, c = st.columns(3)
        datos = {"titulo": a.text_input("Título de la vacante *", key="pub_tit"), "ciudad": b.text_input("Ciudad", key="pub_ciu"),
                 "modalidad": c.selectbox("Modalidad", MODALIDADES, key="pub_mod"),
                 "nivel": a.selectbox("Nivel", NIVELES, index=1, key="pub_niv"),
                 "salario": b.number_input("Salario (COP)", 0, 100_000_000, 5_000_000, step=500_000, key="pub_sal")}
        datos["descripcion"] = st.text_area("Descripción", key="pub_desc", height=80)
        st.markdown("**Habilidades requeridas** (relación `REQUIERE`)")
        filas = st.data_editor(
            [{"habilidad": None, "nivel_minimo": 3, "obligatoria": True}],
            num_rows="dynamic", use_container_width=True, key="pub_req",
            column_config={
                "habilidad": st.column_config.SelectboxColumn("Habilidad", options=opciones_habilidades(), required=True),
                "nivel_minimo": st.column_config.NumberColumn("Nivel mínimo", min_value=1, max_value=5, step=1),
                "obligatoria": st.column_config.CheckboxColumn("Obligatoria"),
            })
        if st.button("Publicar oferta", type="primary") and eid:
            reqs = [f for f in filas if f.get("habilidad")]
            r = ejecutar(cat.crear_oferta, eid, datos, reqs, exito="Oferta publicada")
            if r:
                refrescar(); st.success(f'Oferta `{r["id"]}` publicada por **{r["empresa"]}** con {r["habilidades"]} habilidades requeridas.')
        ver_cypher(cat.Q_CREAR_OFERTA)

    # ------------------------------------------------------------ Requisitos
    with t[3]:
        oid = _sel("Oferta", opciones_ofertas(False), "req_of")
        if oid:
            o = next(x for x in cat.listar_ofertas(False) if x["id"] == oid)
            tabla(o["requisitos"], {"habilidad": "Habilidad", "nivel_minimo": "Nivel mínimo", "obligatoria": "Obligatoria"})
            a, b, c, d = st.columns([2, 1, 1, 1])
            h = a.selectbox("Habilidad", opciones_habilidades(), key="req_h")
            n = b.number_input("Nivel mínimo", 1, 5, 3, key="req_n")
            ob = c.checkbox("Obligatoria", True, key="req_o")
            d.write("")
            if d.button("Agregar / actualizar", type="primary", key="req_btn"):
                ejecutar(cat.agregar_requisito, oid, h, n, ob, exito="Requisito guardado"); refrescar(); st.rerun()
            if o["requisitos"]:
                q = st.selectbox("Quitar requisito", [r["habilidad"] for r in o["requisitos"]], key="req_q")
                if st.button("Quitar requisito", key="req_qbtn"):
                    ejecutar(cat.quitar_requisito, oid, q, exito="Requisito eliminado"); refrescar(); st.rerun()
            ver_cypher(cat.Q_AGREGAR_REQUISITO, cat.Q_QUITAR_REQUISITO)

    # ------------------------------------------------------------ Postulaciones
    with t[4]:
        a, b = st.columns(2)
        with a:
            st.markdown("**Postularse a una oferta**")
            uid = _sel("Profesional", opciones_usuarios(), "pos_u")
            oid = _sel("Oferta activa", opciones_ofertas(True), "pos_o")
            if st.button("Enviar postulación", type="primary") and uid and oid:
                r = ejecutar(us.postular, uid, oid)
                if r:
                    refrescar(); st.success(f'{r["usuario"]} → {r["oferta"]}: **{r["estado"]}** ({r["fecha"]})')
                elif r is None:
                    st.error("La oferta no existe o está cerrada.")
            ver_cypher(us.Q_POSTULAR)
        with b:
            st.markdown("**Postulantes por oferta**")
            oid2 = _sel("Oferta", opciones_ofertas(False), "pos_ver")
            if oid2:
                post = cat.postulantes(oid2)
                tabla(post, {"nombre": "Postulante", "titular": "Titular", "estado": "Estado", "fecha": "Fecha",
                             "habilidades_cumplidas": "Habilidades cumplidas", "habilidades_requeridas": "Requeridas"})
                if post:
                    pid = st.selectbox("Postulante", [p["id"] for p in post],
                                       format_func=lambda i: next(p["nombre"] for p in post if p["id"] == i), key="pos_pid")
                    c1, c2, c3 = st.columns([2, 1, 1])
                    est = c1.selectbox("Nuevo estado", ESTADOS, key="pos_est")
                    c2.write(""); c3.write("")
                    if c2.button("Actualizar", key="pos_upd"):
                        ejecutar(us.cambiar_estado_postulacion, pid, oid2, est, exito="Estado actualizado"); refrescar(); st.rerun()
                    if c3.button("Retirar", key="pos_del"):
                        ejecutar(us.retirar_postulacion, pid, oid2, exito="Postulación retirada"); refrescar(); st.rerun()
                ver_cypher(cat.Q_POSTULANTES, us.Q_ESTADO_POSTULACION, us.Q_RETIRAR_POSTULACION)
