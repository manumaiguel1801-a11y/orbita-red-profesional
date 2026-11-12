"""Mi empresa (reclutador / admin): publicar y gestionar ofertas, postulantes y candidatos recomendados."""
import streamlit as st

from orbita import catalogo as cat
from orbita import recomendaciones as rec
from orbita import usuarios as us
from ui import estilo, sesion
from ui.comun import ejecutar, opciones_empresas, opciones_habilidades, refrescar, ver_cypher
from ui.estilo import esc, pesos, pills
from ui.perfil_pg import ESTADO_COLOR
from ui.perfil_publico import boton_ver_perfil

MODALIDADES = ["Presencial", "Híbrido", "Remoto"]
NIVELES = ["Practicante", "Junior", "Semi Senior", "Senior", "Líder"]
ESTADOS = ["Enviada", "En revisión", "Entrevista", "Oferta", "Rechazada"]


def _empresa(yo: str):
    if sesion.es_admin():
        ops = opciones_empresas()
        return st.selectbox("Empresa (vista de administrador)", list(ops), format_func=lambda i: ops[i], key="rc_emp")
    empresas = cat.empresas_actuales(yo)
    if not empresas:
        estilo.vacio("empresa", "No tienes una empresa actual",
                     "Agrega tu empleo actual en Mi perfil → Experiencia para gestionar las ofertas de tu empresa.")
        return None
    if len(empresas) == 1:
        return empresas[0]["id"]
    return st.selectbox("Empresa", [e["id"] for e in empresas], format_func=lambda i: next(e["nombre"] for e in empresas if e["id"] == i))


def _publicar(yo: str, eid: str):
    with st.container(border=True):
        a, b, c = st.columns(3)
        datos = {"titulo": a.text_input("Título de la vacante *", key="rc_tit", max_chars=120),
                 "ciudad": b.text_input("Ciudad", key="rc_ciu", max_chars=60),
                 "modalidad": c.selectbox("Modalidad", MODALIDADES, key="rc_mod"),
                 "nivel": a.selectbox("Nivel", NIVELES, index=1, key="rc_niv"),
                 "salario": b.number_input("Salario mensual (COP)", 0, 200_000_000, 5_000_000, step=500_000, key="rc_sal")}
        datos["descripcion"] = st.text_area("Descripción del cargo", key="rc_desc", height=90, max_chars=2000)
        estilo.html('<div class="ox-t" style="margin-top:.4rem">Habilidades requeridas</div>'
                    '<div class="ox-s">Las obligatorias pesan el doble en la compatibilidad de los candidatos.</div>')
        filas = st.data_editor(
            [{"habilidad": None, "nivel_minimo": 3, "obligatoria": True}], num_rows="dynamic", use_container_width=True, key="rc_req",
            column_config={"habilidad": st.column_config.SelectboxColumn("Habilidad", options=opciones_habilidades(), required=True),
                           "nivel_minimo": st.column_config.NumberColumn("Nivel mínimo (1-5)", min_value=1, max_value=5, step=1),
                           "obligatoria": st.column_config.CheckboxColumn("Obligatoria")})
        if st.button("Publicar oferta", type="primary", key="rc_pub"):
            r = ejecutar(cat.publicar_oferta_como, yo, eid, datos, [f for f in filas if f.get("habilidad")])
            if r:
                refrescar(); st.success(f"Oferta publicada con {r['habilidades']} habilidades requeridas. Revise los candidatos recomendados.")
    ver_cypher(cat.Q_PUEDE_PUBLICAR, cat.Q_CREAR_OFERTA)


def _mis_ofertas(yo: str, ofertas: list[dict]):
    if not ofertas:
        estilo.vacio("lista", "Su empresa no tiene ofertas publicadas", "Use la pestaña «Publicar oferta».")
    for o in ofertas:
        with st.container(border=True):
            req = [f'{r["habilidad"]} ≥{r["nivel_minimo"]}' + ("" if r["obligatoria"] else " (deseable)") for r in o["requisitos"]]
            estado = pills(["Activa"], "ok") if o["activa"] else pills(["Cerrada"], "no")
            estilo.html(estilo.tarjeta_oferta(o["titulo"], o["empresa"], [o["ciudad"] or "—", o["modalidad"] or "—", o["nivel"] or "—",
                                                                         pesos(o["salario"]), f'{o["postulantes"]} postulantes'],
                                              f'<div class="ox-meta">{estado}{pills(req, "ind")}</div>'))
            with st.expander("Editar oferta y requisitos"):
                with st.form(f"rc_ed_{o['id']}"):
                    a, b, c = st.columns(3)
                    datos = {"titulo": a.text_input("Título", o["titulo"], max_chars=120), "ciudad": b.text_input("Ciudad", o["ciudad"] or ""),
                             "modalidad": c.selectbox("Modalidad", MODALIDADES, index=MODALIDADES.index(o["modalidad"]) if o["modalidad"] in MODALIDADES else 0),
                             "nivel": a.selectbox("Nivel", NIVELES, index=NIVELES.index(o["nivel"]) if o["nivel"] in NIVELES else 1),
                             "salario": b.number_input("Salario", 0, 200_000_000, int(o["salario"] or 0), step=500_000),
                             "activa": c.toggle("Oferta activa (recibe postulaciones)", bool(o["activa"]))}
                    if st.form_submit_button("Guardar", type="primary"):
                        if ejecutar(cat.actualizar_oferta_como, yo, o["id"], datos, exito="Oferta actualizada"):
                            refrescar(); st.rerun()
                x, y, z, w = st.columns([2, 1, 1, 1])
                h = x.selectbox("Habilidad", opciones_habilidades(), key=f"rc_h_{o['id']}")
                n = y.number_input("Nivel mín.", 1, 5, 3, key=f"rc_n_{o['id']}")
                ob = z.checkbox("Obligatoria", True, key=f"rc_o_{o['id']}")
                w.write("")
                if w.button("Agregar", key=f"rc_add_{o['id']}"):
                    ejecutar(cat.agregar_requisito_como, yo, o["id"], h, n, ob, exito="Requisito guardado"); refrescar(); st.rerun()
                if o["requisitos"]:
                    q = st.selectbox("Quitar requisito", [r["habilidad"] for r in o["requisitos"]], key=f"rc_q_{o['id']}")
                    if st.button("Quitar", key=f"rc_qb_{o['id']}"):
                        ejecutar(cat.quitar_requisito_como, yo, o["id"], q, exito="Requisito eliminado"); refrescar(); st.rerun()
                st.divider()
                if st.checkbox("Quiero eliminar esta oferta y sus postulaciones", key=f"rc_dc_{o['id']}"):
                    if st.button("Eliminar oferta", key=f"rc_del_{o['id']}"):
                        ejecutar(cat.eliminar_oferta_como, yo, o["id"], exito="Oferta eliminada"); refrescar(); st.rerun()


def _postulantes(yo: str, ofertas: list[dict]):
    if not ofertas:
        estilo.vacio("usuarios", "Sin ofertas", "Publique una oferta para recibir postulaciones.")
        return
    oid = st.selectbox("Oferta", [o["id"] for o in ofertas], format_func=lambda i: next(o["titulo"] for o in ofertas if o["id"] == i), key="rc_pos_o")
    post = cat.postulantes(oid)
    if not post:
        estilo.vacio("bandeja", "Esta oferta aún no tiene postulantes")
    for p in post:
        with st.container(border=True):
            c1, c2 = st.columns([5, 1.6])
            pct = 100 * p["habilidades_cumplidas"] / max(1, p["habilidades_requeridas"])
            c1.markdown(estilo.tarjeta_persona(p["nombre"], p["titular"],
                                               f'<div class="ox-meta">{pills([p["estado"]], ESTADO_COLOR.get(p["estado"], ""))}'
                                               f'{pills(["Postuló " + str(p["fecha"])])}</div>',
                                               estilo.anillo(pct, f'{p["habilidades_cumplidas"]}/{p["habilidades_requeridas"]}')),
                        unsafe_allow_html=True)
            with c2:
                boton_ver_perfil(p["id"], f"rc_vp_{oid}_{p['id']}")
            nuevo = c2.selectbox("Estado", ESTADOS, index=ESTADOS.index(p["estado"]) if p["estado"] in ESTADOS else 0,
                                 key=f"rc_est_{oid}_{p['id']}")
            if nuevo != p["estado"]:
                ejecutar(cat.estado_postulacion_como, yo, oid, p["id"], nuevo, exito=f"Estado: {nuevo}"); refrescar(); st.rerun()


def _candidatos(yo: str, ofertas: list[dict]):
    activas = [o for o in ofertas if o["activa"]]
    if not activas:
        estilo.vacio("objetivo", "Sin ofertas activas", "Los candidatos se recomiendan para ofertas activas.")
        return
    st.caption("Puntaje = 100·(0,7·cobertura de competencias + 0,3·cercanía en la red con su empresa). Excluye a sus empleados actuales.")
    oid = st.selectbox("Oferta", [o["id"] for o in activas], format_func=lambda i: next(o["titulo"] for o in activas if o["id"] == i), key="rc_can_o")
    for c in rec.recomendar_candidatos(oid, 10):
        with st.container(border=True):
            red_txt = (f"Conoce a {', '.join(c['contactos_en_empresa'])}" if c["contactos_en_empresa"]
                       else f"{c['contactos_2do_grado']} contacto(s) de 2.º grado en la empresa" if c["contactos_2do_grado"] else "Sin vínculos con la empresa")
            estilo.html(estilo.tarjeta_persona(
                c["nombre"], c["titular"],
                f'<div class="ox-meta">{estilo.pills_ok(c["cumple"])}{estilo.pills_no(c["faltan"])}'
                f'{pills(["Ya se postuló"], "ind") if c["ya_postulado"] else ""}</div><div class="ox-s" style="margin-top:.3rem">{estilo.icono("usuarios", 14)} {esc(red_txt)}</div>',
                estilo.anillo(c["puntaje"])))
            boton_ver_perfil(c["id"], f"rc_vc_{oid}_{c['id']}")
    ver_cypher(rec.Q_RECOMENDAR_CANDIDATOS)


def pagina():
    yo = sesion.uid()
    estilo.encabezado("Mi empresa", "Publique vacantes, gestione postulaciones y descubra candidatos", "objetivo")
    eid = _empresa(yo)
    if not eid:
        return
    ofertas = cat.listar_ofertas(False, eid)
    c = st.columns(4)
    estilo.stat(c[0], sum(o["activa"] for o in ofertas), "Ofertas activas", "maletin", "cian")
    estilo.stat(c[1], len(ofertas), "Ofertas publicadas", "lista", "violeta")
    estilo.stat(c[2], sum(o["postulantes"] for o in ofertas), "Postulaciones", "enviar", "lima")
    entrevistas = sum(1 for o in ofertas for p in cat.postulantes(o["id"]) if p["estado"] == "Entrevista")
    estilo.stat(c[3], entrevistas, "En entrevista", "chat", "naranja")
    st.write("")
    t = st.tabs(["Mis ofertas", "Publicar oferta", "Postulantes", "Candidatos recomendados"])
    with t[0]:
        _mis_ofertas(yo, ofertas)
    with t[1]:
        _publicar(yo, eid)
    with t[2]:
        _postulantes(yo, ofertas)
    with t[3]:
        _candidatos(yo, ofertas)
