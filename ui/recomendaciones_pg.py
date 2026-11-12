"""Recomendaciones de contactos, empleos, colaboradores, candidatos y perfiles similares."""
import streamlit as st

from orbita import recomendaciones as rec
from orbita import red
from orbita import usuarios as us
from orbita import catalogo as cat
from ui import sesion
from ui.comun import (cabecera, chips, ejecutar, opciones_ofertas, opciones_usuarios, refrescar, tabla, tarjeta,
                      ver_cypher)


class _Sujeto:
    """El administrador puede consultar las recomendaciones de cualquier usuario; los demás, solo las propias."""

    def __init__(self):
        self.uo = opciones_usuarios()
        self.yo = sesion.uid()

    def __call__(self, key: str, idx: int = 0):
        if sesion.es_admin():
            ids = list(self.uo)
            pref = ids.index(self.yo) if self.yo in ids else min(idx, len(ids) - 1)
            return st.selectbox("Profesional (vista de administrador)", ids, format_func=lambda i: self.uo[i], key=key, index=pref)
        st.caption(f"Recomendaciones para **{sesion.usuario()['nombre']}**")
        return self.yo


def pagina():
    cabecera("Recomendaciones", "Sugerencias calculadas a partir de la estructura del grafo (criterios reproducibles)", "chispa")
    t = st.tabs(["Contactos", "Empleos", "Colaboradores", "Candidatos para una oferta", "Habilidades similares"])
    sujeto = _Sujeto()
    yo = sesion.uid()
    limite = st.sidebar.slider("Resultados por recomendación", 3, 20, 8, key="rec_lim")

    with t[0]:
        st.info("**Puntaje** = 3·contactos en común + 2·habilidades compartidas + 2·misma empresa actual + 2·proyectos compartidos. "
                "Solo personas aún no conectadas.", icon=":material/functions:")
        uid = sujeto("rc_u", 7)
        enviadas = {i["id"] for i in us.invitaciones_enviadas(uid)}
        for r in rec.recomendar_contactos(uid, limite):
            cuerpo = (f'<b>{r["contactos_en_comun"]}</b> contactos en común: ' + chips(r["comunes"][:6])
                      + "<br>Habilidades compartidas: " + chips(r["habilidades_compartidas"], "azul"))
            if r["empresa_compartida"]:
                cuerpo += "<br>Misma empresa: " + chips(r["empresa_compartida"], "ok")
            if r["proyectos_compartidos"]:
                cuerpo += "<br>Proyectos compartidos: " + chips(r["proyectos_compartidos"], "ok")
            c1, c2 = st.columns([6, 1])
            with c1:
                tarjeta(r["nombre"], r["titular"], cuerpo, puntaje=f'{r["puntaje"]} pts')
            if uid != yo:
                continue  # el administrador solo consulta; las invitaciones las envía cada usuario
            if r["id"] in enviadas:
                c2.button("Pendiente", key=f"con_{uid}_{r['id']}", disabled=True, help="Invitación pendiente")
            elif c2.button("Conectar", key=f"con_{uid}_{r['id']}"):
                if ejecutar(us.enviar_invitacion, uid, r["id"], exito="Invitación enviada"):
                    refrescar(); st.rerun()
        ver_cypher(rec.Q_RECOMENDAR_CONTACTOS)

    with t[1]:
        st.info("**Cobertura** = Σ pesos de habilidades cubiertas / Σ pesos requeridos (obligatoria = 2, deseable = 1; "
                "nivel por debajo del mínimo = mitad). **Red** = min(1, (contactos directos en la empresa + 0.5·contactos de 2.º grado) / 3). "
                "**Puntaje** = 100·(0.7·cobertura + 0.3·red).", icon=":material/functions:")
        uid = sujeto("re_u", 42)
        for r in rec.recomendar_empleos(uid, limite):
            cuerpo = ("Cumple: " + chips(r["cumple"], "ok") + " Le falta: " + chips(r["faltan"], "falta")
                      + f'<br>Cobertura de habilidades: <b>{r["cobertura_pct"]}%</b> · Contactos en la empresa: '
                      + (chips(r["contactos_en_empresa"], "azul") or "ninguno") + f' · 2.º grado: {r["contactos_2do_grado"]}')
            c1, c2 = st.columns([6, 1])
            with c1:
                tarjeta(r["oferta"], f'{r["empresa"]} · {r["ciudad"]} · {r["modalidad"]}', cuerpo, puntaje=f'{r["puntaje"]} / 100')
            if uid == yo and c2.button("Postularme", key=f"pos_{uid}_{r['oferta_id']}"):
                if ejecutar(us.postular, uid, r["oferta_id"], exito="Postulación enviada"):
                    refrescar(); st.rerun()
        ver_cypher(rec.Q_RECOMENDAR_EMPLEOS)

    with t[2]:
        st.info("Colaboradores para los proyectos del profesional. **Puntaje** = 2·tecnologías de sus proyectos que domina el candidato "
                "+ 3 si ya están conectados + 1 por cada contacto en común. Excluye a quienes ya comparten proyecto.", icon=":material/functions:")
        uid = sujeto("rcol_u")
        res = rec.recomendar_colaboradores(uid, limite)
        if not res:
            st.warning("Este profesional no participa en proyectos con tecnologías registradas.")
        for r in res:
            tarjeta(r["nombre"], r["titular"], "Aporta: " + chips(r["tecnologias_que_aporta"], "ok")
                    + f'<br>{"Ya conectados" if r["conectado"] else "No conectados"} · {r["contactos_en_comun"]} contactos en común',
                    puntaje=f'{r["puntaje"]} pts')
        ver_cypher(rec.Q_RECOMENDAR_COLABORADORES_USUARIO)

    with t[3]:
        st.markdown("**¿Qué candidatos podrían recomendarse para una oferta según sus conexiones y competencias?**")
        st.info("Misma fórmula que empleos: **Puntaje** = 100·(0.7·cobertura de competencias + 0.3·cercanía en la red con la empresa). "
                "Excluye a quienes ya trabajan en la empresa.", icon=":material/functions:")
        if not sesion.es_reclutador():
            st.info("Esta recomendación está disponible para reclutadores y administradores.")
            oo = {}
        elif sesion.es_admin():
            oo = opciones_ofertas(True)
        else:
            mias = {e["id"] for e in cat.empresas_actuales(yo)}
            oo = {o["id"]: o["titulo"] for o in cat.listar_ofertas(True) if o["empresa_id"] in mias}
            if not oo:
                st.info("Su empresa actual no tiene ofertas activas.")
        oid = st.selectbox("Oferta", list(oo), format_func=lambda i: oo[i], key="cand_o", index=min(18, len(oo) - 1)) if oo else None
        res = rec.recomendar_candidatos(oid, limite) if oid else []
        tabla(res, {"nombre": "Candidato", "titular": "Titular", "puntaje": "Puntaje", "cobertura_pct": "Cobertura %",
                    "cumple": "Cumple", "faltan": "Le falta", "contactos_en_empresa": "Contactos en la empresa",
                    "contactos_2do_grado": "Contactos 2.º grado", "ya_postulado": "¿Ya postulado?"})
        if res:
            import plotly.express as px
            fig = px.bar(res[::-1], x="puntaje", y="nombre", orientation="h", color="cobertura_pct",
                         labels={"puntaje": "Puntaje", "nombre": "", "cobertura_pct": "Cobertura %"})
            fig.update_layout(height=60 + 34 * len(res), margin=dict(l=0, r=0, t=10, b=0))
            st.plotly_chart(fig, use_container_width=True)
        ver_cypher(rec.Q_RECOMENDAR_CANDIDATOS)

    with t[4]:
        st.markdown("**¿Qué usuarios tienen habilidades similares?** — Similitud de Jaccard = |A ∩ B| / |A ∪ B|")
        uid = sujeto("sim_u")
        tabla(red.usuarios_similares(uid, limite), {"nombre": "Profesional", "titular": "Titular", "compartidas": "Habilidades compartidas",
                                                    "en_comun": "En común", "jaccard": "Jaccard", "ya_conectados": "¿Conectados?"})
        ver_cypher(red.Q_USUARIOS_SIMILARES)
        st.markdown("**Pares de profesionales más similares en toda la red**")
        minimo = st.slider("Mínimo de habilidades compartidas", 1, 6, 3, key="sim_min")
        tabla(red.pares_similares(minimo, 20), {"usuario_a": "Profesional A", "usuario_b": "Profesional B",
                                                "compartidas": "Habilidades compartidas", "en_comun": "En común", "jaccard": "Jaccard"})
        ver_cypher(red.Q_PARES_SIMILARES)
