"""Empleos: recomendados, búsqueda con filtros y mis postulaciones."""
import streamlit as st

from orbita import catalogo as cat
from orbita import recomendaciones as rec
from orbita import usuarios as us
from ui import estilo, sesion
from ui.comun import ejecutar, opciones_habilidades, refrescar
from ui.estilo import esc, pesos, pills
from ui.perfil_pg import ESTADO_COLOR


def _postular(yo: str, oferta_id: str, key: str, postulado: bool = False):
    if postulado:
        st.button("Postulado", key=key, disabled=True, use_container_width=True)
    elif st.button("Postularme", key=key, type="primary", use_container_width=True):
        if ejecutar(us.postular, yo, oferta_id, exito="¡Postulación enviada!"):
            refrescar(); st.rerun()


def pagina():
    yo = sesion.uid()
    estilo.encabezado("Empleos", "Vacantes recomendadas según tus habilidades y tu red", "maletin")
    t = st.tabs(["Recomendados para ti", "Buscar ofertas", "Mis postulaciones"])

    with t[0]:
        st.caption("Compatibilidad = 70 % competencias (obligatorias pesan el doble; nivel bajo el mínimo cuenta la mitad) "
                   "+ 30 % red (contactos directos o de 2.º grado en la empresa).")
        recs = rec.recomendar_empleos(yo, 10)
        if not recs:
            estilo.vacio("habilidad", "Aún no tenemos recomendaciones", "Agrega habilidades en Mi perfil para que podamos sugerirte vacantes.")
        for o in recs:
            with st.container(border=True):
                c1, c2 = st.columns([6, 1.3])
                red_txt = (f"Conoces a {', '.join(o['contactos_en_empresa'])}" if o["contactos_en_empresa"]
                           else f"{o['contactos_2do_grado']} contacto(s) de 2.º grado" if o["contactos_2do_grado"] else "")
                c1.markdown(estilo.tarjeta_oferta(
                    o["oferta"], o["empresa"], [("ubicacion", o['ciudad']), ("maletin", o["modalidad"]), ("habilidad", f"Competencias {o['cobertura_pct']:.0f}%")],
                    f'<div class="ox-meta">{estilo.pills_ok(o["cumple"])}{estilo.pills_no(o["faltan"])}</div>'
                    + (f'<div class="ox-s" style="margin-top:.35rem">{esc(red_txt)}</div>' if red_txt else ""),
                    estilo.anillo(o["puntaje"])), unsafe_allow_html=True)
                with c2:
                    st.write("")
                    _postular(yo, o["oferta_id"], f"e_rec_{o['oferta_id']}")

    with t[1]:
        f1, f2, f3, f4 = st.columns([2.2, 1, 1, 2])
        texto = f1.text_input("Cargo o empresa", placeholder="Ej.: Datos, Pacífico Cloud…", key="e_txt")
        modalidad = f2.selectbox("Modalidad", ["", "Presencial", "Híbrido", "Remoto"], format_func=lambda m: m or "Todas", key="e_mod")
        ofertas_all = cat.listar_ofertas(True)
        ciudades = [""] + sorted({o["ciudad"] for o in ofertas_all if o["ciudad"]})
        ciudad = f3.selectbox("Ciudad", ciudades, format_func=lambda c: c or "Todas", key="e_ciu")
        habs = f4.multiselect("Que requieran", opciones_habilidades(), key="e_habs")
        res = cat.buscar_ofertas(yo, texto, modalidad, ciudad, habs)
        st.caption(f"{len(res)} oferta(s) activas")
        if not res:
            estilo.vacio("buscar", "No hay ofertas con esos filtros", "Pruebe ampliando la búsqueda.")
        for o in res:
            with st.container(border=True):
                c1, c2 = st.columns([6, 1.3])
                tengo = sum(r["tengo"] for r in o["requisitos"])
                req = "".join(pills([("" if r["tengo"] else "") + r["habilidad"] + ("" if r["obligatoria"] else " (deseable)")],
                                    "ok" if r["tengo"] else "") for r in o["requisitos"])
                c1.markdown(estilo.tarjeta_oferta(
                    o["titulo"], o["empresa"], [("ubicacion", o['ciudad']), ("maletin", o["modalidad"]), o["nivel"], pesos(o["salario"]),
                                                ("usuarios", f"{o['postulantes']} postulantes"), ("calendario", f"Publicada {o['fecha_publicacion']}")],
                    f'<div class="ox-meta">{req}</div><div class="ox-s" style="margin-top:.35rem">Cumples {tengo} de {len(o["requisitos"])} habilidades</div>'),
                    unsafe_allow_html=True)
                with c2:
                    st.write("")
                    _postular(yo, o["id"], f"e_bus_{o['id']}", o["postulado"])

    with t[2]:
        p = us.obtener_usuario(yo)
        etapas = ["Enviada", "En revisión", "Entrevista", "Oferta", "Rechazada"]
        c = st.columns(len(etapas))
        for i, e in enumerate(etapas):
            estilo.stat(c[i], sum(x["estado"] == e for x in p["postulaciones"]), e, ["enviar", "ojo", "chat", "trofeo", "cerrar"][i],
                        ["gris", "naranja", "#E0E7FF", "lima", "rosa"][i])
        st.write("")
        if not p["postulaciones"]:
            estilo.vacio("enviar", "Aún no te has postulado", "Explora las recomendaciones para encontrar tu próxima oportunidad.")
        for x in p["postulaciones"]:
            with st.container(border=True):
                c1, c2 = st.columns([6, 1.3])
                c1.markdown(estilo.tarjeta_oferta(x["oferta"], x["empresa"], [("calendario", f"Enviada {x['fecha']}")],
                                                  f'<div class="ox-meta">{pills([x["estado"]], ESTADO_COLOR.get(x["estado"], ""))}</div>'),
                            unsafe_allow_html=True)
                if c2.button("Retirar", key=f"e_ret_{x['oferta_id']}", use_container_width=True):
                    ejecutar(us.retirar_postulacion, yo, x["oferta_id"], exito="Postulación retirada"); refrescar(); st.rerun()
