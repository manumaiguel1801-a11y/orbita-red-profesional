"""Mi perfil: vista pública, edición validada, habilidades, experiencia, proyectos, postulaciones y seguridad."""
from datetime import date

import streamlit as st

from orbita import catalogo as cat
from orbita import seguridad
from orbita import usuarios as us
from ui import estilo, sesion
from ui.comun import (categorias_habilidad, ejecutar, opciones_empresas, opciones_habilidades, opciones_proyectos,
                      refrescar, tabla)
from ui.estilo import esc, pills
from ui.inicio import completitud

NIVELES_EDU = ["", "Bachillerato", "Técnico", "Tecnólogo", "Pregrado", "Especialización", "Maestría", "Doctorado"]
NIVEL_TXT = {1: "Básico", 2: "Inicial", 3: "Intermedio", 4: "Avanzado", 5: "Experto"}
ESTADO_COLOR = {"Enviada": "", "En revisión": "warn", "Entrevista": "ind", "Oferta": "ok", "Rechazada": "no"}


def _cabecera(p: dict, pct: int):
    u = p["usuario"]
    actual = next((e for e in p["empresas"] if e["actual"]), None)
    estilo.html(f"""<div class="ox-card" style="padding:0;overflow:hidden">
      <div style="height:92px;background:linear-gradient(120deg,#2E1065,#6D28D9 50%,#8B5CF6 75%,#A3E635 140%)"></div>
      <div style="padding:0 1.4rem 1.2rem;margin-top:-44px" class="ox-row">
        <div style="border:4px solid #0F0F13;border-radius:50%">{estilo.avatar(u['nombre'], 92)}</div>
        <div style="flex:1;padding-top:50px">
          <div class="ox-t" style="font-size:1.35rem">{esc(u['nombre'])} &nbsp;{estilo.badge_rol(u.get('rol', 'profesional'))}</div>
          <div class="ox-s" style="font-size:.95rem;color:#D4D4D8">{esc(u.get('titular') or 'Sin titular')}{' · ' + esc(actual['empresa']) if actual else ''}</div>
          <div class="ox-meta">{pills([("ubicacion", u.get('ciudad') or 'Sin ciudad'), ("correo", u.get('email')), ("birrete", u.get('nivel_educativo') or '—'),
                                     ("reloj", f"{u.get('anios_experiencia') or 0} años"), ("conexion", f"{len(p['conexiones'])} conexiones")])}</div>
        </div>
        <div style="padding-top:56px;text-align:center">{estilo.anillo(pct)}<div class="ox-s">Perfil</div></div>
      </div></div>""")


def _resumen(p: dict):
    u = p["usuario"]
    izq, der = st.columns([1.6, 1], gap="large")
    with izq:
        with st.container(border=True):
            estilo.html('<div class="ox-t">Acerca de</div>')
            st.write(u.get("resumen") or "_Aún no ha escrito un resumen profesional._")
        with st.container(border=True):
            estilo.html('<div class="ox-t">Experiencia</div>')
            if not p["empresas"]:
                st.caption("Sin experiencia registrada.")
            for e in sorted(p["empresas"], key=lambda e: (not e["actual"], -(e["desde"] or 0))):
                estilo.html(f'<div class="ox-row" style="margin:.6rem 0">{estilo.logo_empresa(e["empresa"])}<div>'
                            f'<div class="ox-t" style="font-size:.95rem">{esc(e["cargo"])}</div>'
                            f'<div class="ox-s">{esc(e["empresa"])} · desde {e["desde"]} {"· <b style=color:#A3E635>Actual</b>" if e["actual"] else ""}</div></div></div>')
        with st.container(border=True):
            estilo.html('<div class="ox-t">Proyectos</div>')
            if not p["proyectos"]:
                st.caption("Sin proyectos.")
            estilo.html(pills([f'{x["proyecto"]} · {x["rol"]}' for x in p["proyectos"]], "ind"))
    with der:
        with st.container(border=True):
            estilo.html('<div class="ox-t">Habilidades</div>')
            if not p["habilidades"]:
                st.caption("Agregue habilidades en la pestaña Habilidades.")
            for h in sorted(p["habilidades"], key=lambda h: -(h["nivel"] or 0)):
                estilo.html(f'<div style="margin:.45rem 0"><div style="display:flex;justify-content:space-between;font-size:.88rem">'
                            f'<b>{esc(h["habilidad"])}</b><span class="ox-s">{NIVEL_TXT.get(h["nivel"], "")}</span></div>'
                            f'{estilo.barra((h["nivel"] or 0) * 20)}</div>')


def _editar(p: dict):
    u = p["usuario"]
    errores = st.session_state.get("err_perfil", {})
    with st.form("form_perfil"):
        c1, c2 = st.columns(2)
        datos = {
            "nombre": c1.text_input("Nombre y apellido *", u.get("nombre", "")),
            "email": c2.text_input("Correo electrónico *", u.get("email", "")),
            "titular": c1.text_input("Titular profesional", u.get("titular") or "", max_chars=120),
            "ciudad": c2.text_input("Ciudad", u.get("ciudad") or "", max_chars=60),
            "telefono": c1.text_input("Teléfono", u.get("telefono") or "", placeholder="+57 300 000 0000"),
            "anios_experiencia": c2.number_input("Años de experiencia", 0, 60, int(u.get("anios_experiencia") or 0)),
            "nivel_educativo": c1.selectbox("Nivel educativo", NIVELES_EDU, index=NIVELES_EDU.index(u.get("nivel_educativo"))
                                            if u.get("nivel_educativo") in NIVELES_EDU else 0),
        }
        datos["resumen"] = st.text_area("Resumen profesional", u.get("resumen") or "", max_chars=1000, height=120,
                                        help="Cuente en 2-4 frases su experiencia y lo que busca.")
        for campo, msg in errores.items():
            st.error(f"**{campo.replace('_', ' ').capitalize()}:** {msg}")
        if st.form_submit_button("Guardar cambios", type="primary"):
            err = seguridad.validar_perfil(datos)
            if not err and datos["email"].strip().lower() != u["email"] and us.email_en_uso_por_otro(datos["email"], u["id"]):
                err["email"] = "Ese correo ya está registrado por otra cuenta."
            st.session_state["err_perfil"] = err
            if not err and ejecutar(us.actualizar_usuario, u["id"], datos, exito="Perfil actualizado"):
                st.session_state["usuario"]["nombre"] = " ".join(datos["nombre"].split())
                refrescar()
            st.rerun()


def _habilidades(p: dict, uid: str):
    a, b, c = st.columns([2.2, 1.4, 1])
    opciones = opciones_habilidades()
    hab = a.selectbox("Habilidad", opciones + ["Otra habilidad…"], key="pf_hab")
    cat_nueva = None
    if hab == "Otra habilidad…":
        hab = a.text_input("Nombre de la habilidad", key="pf_hab_n", max_chars=60).strip()
        cat_nueva = a.selectbox("Categoría", categorias_habilidad(), key="pf_hab_c")
    nivel = b.select_slider("Nivel", options=[1, 2, 3, 4, 5], value=3, format_func=lambda n: f"{n} · {NIVEL_TXT[n]}", key="pf_niv")
    c.write(""); c.write("")
    if c.button("Agregar", type="primary", key="pf_hab_btn", use_container_width=True):
        if not hab or len(hab) < 1:
            st.error("Indique el nombre de la habilidad.")
        elif any(h["habilidad"].lower() == hab.lower() and h["habilidad"] != hab for h in p["habilidades"]):
            st.error("Ya tiene esa habilidad.")
        elif ejecutar(us.asignar_habilidad, uid, hab, nivel, cat_nueva, exito=f"{hab} guardada"):
            refrescar(); st.rerun()
    if not p["habilidades"]:
        estilo.vacio("habilidad", "Sin habilidades todavía", "Las habilidades alimentan tus recomendaciones de empleo y contactos.")
    for h in sorted(p["habilidades"], key=lambda h: -(h["nivel"] or 0)):
        with st.container(border=True):
            x, y, z = st.columns([3, 2, 0.7])
            x.markdown(f"**{h['habilidad']}**  \n<span class='ox-s'>{h['categoria']}</span>", unsafe_allow_html=True)
            nuevo = y.select_slider("Nivel", [1, 2, 3, 4, 5], value=h["nivel"] or 3, key=f"pf_n_{h['habilidad']}",
                                    format_func=lambda n: NIVEL_TXT[n], label_visibility="collapsed")
            if nuevo != h["nivel"]:
                ejecutar(us.asignar_habilidad, uid, h["habilidad"], nuevo); refrescar(); st.rerun()
            if z.button("Quitar", icon=":material/delete:", key=f"pf_q_{h['habilidad']}", help="Quitar habilidad"):
                ejecutar(us.quitar_habilidad, uid, h["habilidad"], exito="Habilidad retirada"); refrescar(); st.rerun()


OTRA_EMPRESA = "__otra__"
_CAMPOS_EXP = ["pf_emp", "pf_emp_n", "pf_emp_s", "pf_emp_c", "pf_cargo", "pf_desde", "pf_actual"]


def _experiencia(p: dict, uid: str):
    with st.container(border=True):
        estilo.html(f'<div class="ox-t">{estilo.icono("mas", 17)} Agregar experiencia</div>')
        emps = opciones_empresas()
        c1, c2 = st.columns(2)
        emp = c1.selectbox("Empresa *", list(emps) + [OTRA_EMPRESA], key="pf_emp",
                           format_func=lambda i: emps.get(i, "Otra empresa (no está en la lista)…"),
                           help="Escriba para buscar. Si su empresa no aparece, elija «Otra empresa» al final de la lista.")
        cargo = c2.text_input("Cargo *", max_chars=80, key="pf_cargo", placeholder="Ej.: Analista de Datos")
        nueva = {}
        if emp == OTRA_EMPRESA:
            n1, n2, n3 = st.columns(3)
            nueva = {"nombre": n1.text_input("Nombre de la empresa *", max_chars=80, key="pf_emp_n"),
                     "sector": n2.text_input("Sector", max_chars=60, key="pf_emp_s", placeholder="Ej.: Tecnología"),
                     "ciudad": n3.text_input("Ciudad", max_chars=60, key="pf_emp_c")}
            if nueva["nombre"].strip() and (ya := cat.buscar_empresa_por_nombre(nueva["nombre"])):
                st.info(f"Ya existe **{ya['nombre']}** en Órbita: se usará esa empresa.", icon=":material/info:")
        d1, d2 = st.columns(2)
        desde = d1.number_input("Desde (año)", 1970, date.today().year, date.today().year, key="pf_desde")
        d2.write("")
        actual = d2.checkbox("Es mi empleo actual", True, key="pf_actual")
        if st.button("Agregar experiencia", type="primary", key="pf_exp_btn"):
            if len(cargo.strip()) < 2:
                st.error("Indique el cargo (mínimo 2 caracteres).")
                return
            empresa_id = emp
            if emp == OTRA_EMPRESA:
                e = ejecutar(cat.registrar_empresa, nueva)
                if not e:
                    return
                empresa_id = e["id"]
            if ejecutar(us.vincular_empresa, uid, empresa_id, cargo.strip(), desde, actual, exito="Experiencia guardada"):
                for k in _CAMPOS_EXP:
                    st.session_state.pop(k, None)
                refrescar(); st.rerun()
    for e in sorted(p["empresas"], key=lambda e: (not e["actual"], -(e["desde"] or 0))):
        with st.container(border=True):
            x, z = st.columns([6, 1])
            x.markdown(estilo.tarjeta_persona(e["empresa"], f'{e["cargo"]} · desde {e["desde"]}' + (" · Actual" if e["actual"] else "")),
                       unsafe_allow_html=True)
            if z.button("Quitar", icon=":material/delete:", key=f"pf_e_{e['empresa_id']}", help="Quitar experiencia"):
                ejecutar(us.desvincular_empresa, uid, e["empresa_id"], exito="Experiencia eliminada"); refrescar(); st.rerun()


def _proyectos(p: dict, uid: str):
    a, b = st.columns(2, gap="large")
    with a, st.container(border=True):
        estilo.html('<div class="ox-t">Unirme a un proyecto existente</div>')
        mios = {x["proyecto_id"] for x in p["proyectos"]}
        ops = {k: v for k, v in opciones_proyectos().items() if k not in mios}
        if ops:
            pid = st.selectbox("Proyecto", list(ops), format_func=lambda i: ops[i], key="pf_pj")
            rol = st.text_input("Mi rol", "Colaborador", key="pf_pj_rol", max_chars=60)
            if st.button("Unirme", type="primary", key="pf_pj_btn"):
                ejecutar(us.vincular_proyecto, uid, pid, rol.strip() or "Colaborador", exito="Te uniste al proyecto"); refrescar(); st.rerun()
    with b, st.container(border=True):
        estilo.html('<div class="ox-t">Crear un proyecto nuevo</div>')
        with st.form("pf_np", clear_on_submit=True, border=False):
            nombre = st.text_input("Nombre *", max_chars=120)
            desc = st.text_area("Descripción", max_chars=500, height=70)
            tecs = st.multiselect("Tecnologías *", opciones_habilidades())
            if st.form_submit_button("Crear proyecto"):
                if ejecutar(cat.crear_proyecto_como, uid, {"nombre": nombre.strip(), "descripcion": desc, "estado": "En curso",
                                                            "anio": date.today().year}, tecs, exito="Proyecto creado"):
                    refrescar(); st.rerun()
    for x in p["proyectos"]:
        with st.container(border=True):
            c1, c2 = st.columns([6, 1])
            c1.markdown(f"**{x['proyecto']}** · {x['rol']}")
            if c2.button("Salir", key=f"pf_sal_{x['proyecto_id']}"):
                ejecutar(us.desvincular_proyecto, uid, x["proyecto_id"], exito="Saliste del proyecto"); refrescar(); st.rerun()


def _postulaciones(p: dict, uid: str):
    if not p["postulaciones"]:
        estilo.vacio("enviar", "Aún no te has postulado", "Revisa la sección Empleos para encontrar vacantes recomendadas.")
    for x in p["postulaciones"]:
        with st.container(border=True):
            c1, c2 = st.columns([6, 1])
            c1.markdown(estilo.tarjeta_oferta(x["oferta"], x["empresa"], [("calendario", f"Enviada {x['fecha']}")],
                                              f'<div class="ox-meta">{pills([x["estado"]], ESTADO_COLOR.get(x["estado"], ""))}</div>'),
                        unsafe_allow_html=True)
            if c2.button("Retirar", key=f"pf_ret_{x['oferta_id']}"):
                ejecutar(us.retirar_postulacion, uid, x["oferta_id"], exito="Postulación retirada"); refrescar(); st.rerun()


def _seguridad(p: dict, uid: str):
    a, b = st.columns(2, gap="large")
    with a, st.container(border=True):
        estilo.html('<div class="ox-t">' + estilo.icono("candado") + ' Cambiar contraseña</div>')
        with st.form("pf_pwd", clear_on_submit=True, border=False):
            actual = st.text_input("Contraseña actual", type="password")
            nueva = st.text_input("Nueva contraseña", type="password", help="8+ caracteres, mayúscula, minúscula, número y símbolo.")
            conf = st.text_input("Confirmar nueva contraseña", type="password")
            if st.form_submit_button("Actualizar contraseña", type="primary"):
                try:
                    seguridad.cambiar_password(uid, actual, nueva, conf, p["usuario"]["email"], p["usuario"]["nombre"])
                except ValueError as e:
                    st.error(str(e))
                else:  # cambiar la contraseña invalida todas las sesiones abiertas
                    sesion.cerrar()
                    st.session_state["aviso_sesion"] = "Contraseña actualizada. Inicie sesión con su nueva contraseña."
                    st.rerun()
        u = p["usuario"]
        st.caption(f"Último acceso: {(u.get('ultimo_acceso') or '—')[:16].replace('T', ' ')} · Miembro desde {u.get('fecha_registro') or '—'}")
    with b, st.container(border=True):
        estilo.html('<div class="ox-t" style="color:#FCA5A5">' + estilo.icono("alerta") + ' Eliminar mi cuenta</div>')
        st.caption("Se eliminarán su perfil, conexiones, habilidades, experiencia, proyectos y postulaciones. No se puede deshacer.")
        pwd = st.text_input("Confirme con su contraseña", type="password", key="pf_del_pwd")
        ok = st.checkbox("Entiendo que esta acción es permanente", key="pf_del_ok")
        if st.button("Eliminar mi cuenta", disabled=not ok, key="pf_del_btn"):
            if p["usuario"].get("rol") == "admin":
                st.error("Un administrador no puede eliminar su propia cuenta desde aquí.")
            elif not seguridad.verificar_password_usuario(uid, pwd):
                st.error("La contraseña no es correcta.")
            else:
                us.eliminar_usuario(uid); sesion.cerrar(); refrescar(); st.rerun()


def pagina():
    uid = sesion.uid()
    p = us.obtener_usuario(uid)
    if not p:
        sesion.cerrar(); st.rerun()
    pct, _ = completitud(p)
    _cabecera(p, pct)
    t = st.tabs(["Resumen", "Editar información", "Habilidades", "Experiencia", "Proyectos",
                 f"Postulaciones ({len(p['postulaciones'])})", "Seguridad"])
    with t[0]:
        _resumen(p)
    with t[1]:
        _editar(p)
    with t[2]:
        _habilidades(p, uid)
    with t[3]:
        _experiencia(p, uid)
    with t[4]:
        _proyectos(p, uid)
    with t[5]:
        _postulaciones(p, uid)
    with t[6]:
        _seguridad(p, uid)
