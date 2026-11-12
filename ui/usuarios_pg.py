"""Página de usuarios: directorio, perfil, CRUD y vínculos (habilidades, empresas, proyectos, conexiones)."""
from datetime import date

import streamlit as st

from orbita import seguridad
from orbita import usuarios as us
from ui import estilo, sesion
from ui.comun import (cabecera, chips, ejecutar, esc, iniciales, opciones_empresas, opciones_habilidades,
                      opciones_proyectos, opciones_usuarios, refrescar, seleccionar, tabla, ver_cypher,
                      categorias_habilidad)

NIVELES_EDU = ["", "Bachillerato", "Técnico", "Tecnólogo", "Pregrado", "Especialización", "Maestría", "Doctorado"]


def _form_usuario(prefijo: str, actual: dict | None = None) -> dict:
    a = actual or {}
    c1, c2 = st.columns(2)
    datos = {
        "nombre": c1.text_input("Nombre completo *", a.get("nombre", ""), key=f"{prefijo}_nombre"),
        "email": c2.text_input("Correo electrónico *", a.get("email", ""), key=f"{prefijo}_email"),
        "titular": c1.text_input("Titular profesional", a.get("titular", ""), key=f"{prefijo}_titular",
                                 placeholder="Ej.: Ingeniera de Datos"),
        "ciudad": c2.text_input("Ciudad", a.get("ciudad", ""), key=f"{prefijo}_ciudad"),
        "telefono": c1.text_input("Teléfono", a.get("telefono", ""), key=f"{prefijo}_telefono"),
        "anios_experiencia": c2.number_input("Años de experiencia", 0, 60, int(a.get("anios_experiencia") or 0), key=f"{prefijo}_anios"),
        "nivel_educativo": c1.selectbox("Nivel educativo", NIVELES_EDU,
                                        index=NIVELES_EDU.index(a.get("nivel_educativo")) if a.get("nivel_educativo") in NIVELES_EDU else 0,
                                        key=f"{prefijo}_edu"),
    }
    datos["resumen"] = st.text_area("Resumen profesional", a.get("resumen", ""), key=f"{prefijo}_resumen", height=90)
    return datos


def _perfil(uid: str):
    p = us.obtener_usuario(uid)
    if not p:
        st.warning("El usuario no existe.")
        return
    u = p["usuario"]
    c1, c2 = st.columns([1, 6])
    c1.markdown(estilo.avatar(u["nombre"], 64), unsafe_allow_html=True)
    actual = [e for e in p["empresas"] if e["actual"]]
    c2.markdown(f'### {esc(u["nombre"])}\n**{esc(u.get("titular") or "")}**'
                + (f' en {esc(actual[0]["empresa"])}' if actual else "")
                + f'  \n{esc(u.get("ciudad") or "—")} · {esc(u.get("email"))} · {esc(u.get("telefono") or "—")} · '
                  f'{esc(u.get("nivel_educativo") or "—")} · {u.get("anios_experiencia") or 0} años')
    if u.get("resumen"):
        st.caption(u["resumen"])
    m = st.columns(5)
    m[0].metric("Conexiones", len(p["conexiones"]))
    m[1].metric("Habilidades", len(p["habilidades"]))
    m[2].metric("Empresas", len(p["empresas"]))
    m[3].metric("Proyectos", len(p["proyectos"]))
    m[4].metric("Postulaciones", len(p["postulaciones"]))
    a, b = st.columns(2)
    with a:
        st.markdown("**Habilidades**")
        st.markdown(chips([f'{h["habilidad"]} · nivel {h["nivel"]}/5' for h in
                           sorted(p["habilidades"], key=lambda h: -(h["nivel"] or 0))], "azul") or "—", unsafe_allow_html=True)
        st.markdown("**Experiencia**")
        tabla(sorted(p["empresas"], key=lambda e: -(e["desde"] or 0)),
              {"empresa": "Empresa", "cargo": "Cargo", "desde": "Desde", "actual": "Actual"})
    with b:
        st.markdown("**Proyectos**")
        tabla(p["proyectos"], {"proyecto": "Proyecto", "rol": "Rol"})
        st.markdown("**Postulaciones**")
        tabla(p["postulaciones"], {"oferta": "Oferta", "empresa": "Empresa", "estado": "Estado", "fecha": "Fecha"})
    st.markdown("**Conexiones**")
    st.markdown(chips([c["nombre"] for c in p["conexiones"]]) or "Sin conexiones todavía.", unsafe_allow_html=True)
    ver_cypher(us.Q_OBTENER_USUARIO)


def pagina():
    cabecera("Usuarios", "Registrar, consultar, actualizar y eliminar profesionales (CRUD) y gestionar sus vínculos", "usuarios")
    t = st.tabs(["Directorio", "Perfil", "Registrar", "Editar", "Eliminar", "Vínculos del perfil", "Cuentas y roles"])
    with t[6]:
        _cuentas()

    with t[0]:
        texto = st.text_input("Buscar por nombre, titular o ciudad", key="dir_buscar", placeholder="Ej.: datos, Medellín, React…")
        filas = us.listar_usuarios(texto)
        st.caption(f"{len(filas)} profesionales encontrados")
        tabla(filas, {"id": "ID", "nombre": "Nombre", "titular": "Titular", "ciudad": "Ciudad", "empresa_actual": "Empresa actual",
                      "anios_experiencia": "Años exp.", "conexiones": "Conexiones", "habilidades": "Habilidades", "email": "Correo"},
              altura=480)
        ver_cypher(us.Q_LISTAR_USUARIOS)

    with t[1]:
        uid = seleccionar("Profesional", opciones_usuarios(), key="perfil_u")
        if uid:
            _perfil(uid)

    with t[2]:
        with st.form("form_crear", clear_on_submit=True):
            datos = _form_usuario("crear")
            temporal = st.text_input("Contraseña temporal (opcional)", type="password", key="crear_tmp",
                                     help="Si la deja vacía, la persona no podrá iniciar sesión hasta que se le asigne una.")
            if st.form_submit_button("Registrar profesional", type="primary"):
                errores = seguridad.validar_perfil(datos)
                if not errores and seguridad.email_registrado(datos["email"]):
                    errores["email"] = "Ya existe una cuenta con ese correo."
                faltas = seguridad.validar_password(temporal) if temporal else []
                if faltas:
                    errores["contraseña temporal"] = "Debe tener " + ", ".join(faltas) + "."
                for campo, msg in errores.items():
                    st.error(f"**{campo.capitalize()}:** {msg}")
                u = None if errores else ejecutar(us.crear_usuario, datos, exito="Profesional registrado")
                if u:
                    if temporal:
                        seguridad.fijar_password_temporal(sesion.uid(), u["id"], temporal)
                    refrescar()
                    st.success(f'Se creó el nodo :Usuario **{u["nombre"]}** con id `{u["id"]}`'
                               + (" y contraseña temporal." if temporal else " (sin contraseña)."))
        ver_cypher(us.Q_CREAR_USUARIO)

    with t[3]:
        uid = seleccionar("Profesional a editar", opciones_usuarios(), key="editar_u")
        if uid:
            actual = us.obtener_usuario(uid)["usuario"]
            with st.form(f"form_editar_{uid}"):
                datos = _form_usuario(f"ed_{uid}", actual)
                if st.form_submit_button("Guardar cambios", type="primary"):
                    if ejecutar(us.actualizar_usuario, uid, datos, exito="Cambios guardados"):
                        refrescar()
                        st.success("Perfil actualizado en Neo4j.")
            ver_cypher(us.Q_ACTUALIZAR_USUARIO)

    with t[4]:
        uid = seleccionar("Profesional a eliminar", opciones_usuarios(), key="eliminar_u")
        if uid:
            p = us.obtener_usuario(uid)
            st.warning(f'Se eliminará **{p["usuario"]["nombre"]}** y todas sus relaciones '
                       f'({len(p["conexiones"])} conexiones, {len(p["habilidades"])} habilidades, '
                       f'{len(p["empresas"])} empresas, {len(p["proyectos"])} proyectos, {len(p["postulaciones"])} postulaciones).')
            conf = st.checkbox("Confirmo que deseo eliminar este profesional", key=f"conf_del_{uid}")
            if st.button("Eliminar definitivamente", type="primary", disabled=not conf, key=f"btn_del_{uid}"):
                n = ejecutar(us.eliminar_usuario, uid, exito="Profesional eliminado")
                if n is not None:
                    refrescar()
                    st.success(f"Usuario eliminado junto con {n} relaciones (DETACH DELETE).")
            ver_cypher(us.Q_ELIMINAR_USUARIO)

    with t[5]:
        _vinculos()


def _cuentas():
    """Administración de cuentas: rol, activación y contraseña temporal."""
    yo = sesion.uid()
    filas = us.listar_usuarios()
    c = st.columns(4)
    estilo.stat(c[0], len(filas), "Cuentas", "usuarios")
    estilo.stat(c[1], sum(f["rol"] == "reclutador" for f in filas), "Reclutadores", "objetivo", "cian")
    estilo.stat(c[2], sum(f["rol"] == "admin" for f in filas), "Administradores", "escudo", "violeta")
    estilo.stat(c[3], sum(not f["activo"] for f in filas), "Desactivadas", "bloqueo", "rosa")
    st.write("")
    tabla(filas, {"nombre": "Nombre", "email": "Correo", "rol": "Rol", "activo": "Activa", "tiene_password": "Con contraseña",
                  "empresa_actual": "Empresa actual", "ultimo_acceso": "Último acceso"}, altura=320)
    uid = seleccionar("Cuenta", opciones_usuarios(), key="cta_u")
    if not uid:
        return
    f = next(x for x in filas if x["id"] == uid)
    a, b, c3 = st.columns(3, gap="large")
    with a, st.container(border=True):
        estilo.html('<div class="ox-t">Rol</div>')
        roles = list(seguridad.ROLES)
        nuevo = st.radio("Rol", roles, index=roles.index(f["rol"]), format_func=seguridad.ROLES.get, key=f"cta_rol_{uid}",
                         label_visibility="collapsed")
        if nuevo == "reclutador" and not f["empresa_actual"]:
            st.caption("Un reclutador necesita una empresa actual para publicar ofertas.")
        if st.button("Guardar rol", key=f"cta_rb_{uid}", type="primary") and nuevo != f["rol"]:
            if ejecutar(seguridad.cambiar_rol, yo, uid, nuevo, exito=f"Rol actualizado: {seguridad.ROLES[nuevo]}"):
                refrescar(); st.rerun()
    with b, st.container(border=True):
        estilo.html('<div class="ox-t">Estado de la cuenta</div>')
        st.write("Activa" if f["activo"] else "Desactivada (no puede iniciar sesión)")
        if st.button("Desactivar" if f["activo"] else "Reactivar", key=f"cta_act_{uid}"):
            if ejecutar(seguridad.activar_cuenta, yo, uid, not f["activo"], exito="Estado actualizado") is not None:
                refrescar(); st.rerun()
    with c3, st.container(border=True):
        estilo.html('<div class="ox-t">Contraseña temporal</div>')
        tmp = st.text_input("Nueva contraseña temporal", type="password", key=f"cta_pw_{uid}")
        if st.button("Asignar", key=f"cta_pwb_{uid}"):
            if ejecutar(seguridad.fijar_password_temporal, yo, uid, tmp, exito="Contraseña asignada"):
                st.success("Contraseña asignada. Las sesiones abiertas de esa cuenta se cerraron.")
    ver_cypher(seguridad.Q_CAMBIAR_ROL, seguridad.Q_ACTIVAR, seguridad.Q_FIJAR_PASSWORD)


def _vinculos():
    uid = seleccionar("Profesional", opciones_usuarios(), key="vinc_u")
    if not uid:
        return
    p = us.obtener_usuario(uid)
    s = st.tabs(["Habilidades", "Empresas", "Proyectos", "Conexiones"])

    with s[0]:
        c1, c2, c3 = st.columns([2, 1, 1])
        existentes = opciones_habilidades()
        hab = c1.selectbox("Habilidad", existentes + ["Nueva habilidad…"], key="v_hab")
        nueva_cat = None
        if hab == "Nueva habilidad…":
            hab = c1.text_input("Nombre de la nueva habilidad", key="v_hab_nueva")
            nueva_cat = c1.selectbox("Categoría", categorias_habilidad(), key="v_hab_cat")
        nivel = c2.slider("Nivel (1-5)", 1, 5, 3, key="v_nivel")
        c3.write("")
        if c3.button("Asignar / actualizar", key="v_hab_btn", type="primary") and hab:
            if ejecutar(us.asignar_habilidad, uid, hab, nivel, nueva_cat, exito="Habilidad asignada"):
                refrescar(); st.rerun()
        tabla(p["habilidades"], {"habilidad": "Habilidad", "categoria": "Categoría", "nivel": "Nivel"})
        if p["habilidades"]:
            q = st.selectbox("Quitar habilidad", [h["habilidad"] for h in p["habilidades"]], key="v_hab_q")
            if st.button("Quitar", key="v_hab_qbtn"):
                ejecutar(us.quitar_habilidad, uid, q, exito="Habilidad retirada"); refrescar(); st.rerun()
        ver_cypher(us.Q_ASIGNAR_HABILIDAD, us.Q_QUITAR_HABILIDAD)

    with s[1]:
        c1, c2, c3, c4 = st.columns([2, 2, 1, 1])
        emp = c1.selectbox("Empresa", list(opciones_empresas()), format_func=lambda i: opciones_empresas()[i], key="v_emp")
        cargo = c2.text_input("Cargo", key="v_cargo", placeholder="Ej.: Desarrolladora Backend")
        desde = c3.number_input("Desde (año)", 1970, date.today().year, date.today().year, key="v_desde")
        actual = c4.checkbox("Empleo actual", True, key="v_actual")
        if st.button("Vincular con la empresa", type="primary", key="v_emp_btn"):
            if not cargo:
                st.error("Indique el cargo.")
            elif ejecutar(us.vincular_empresa, uid, emp, cargo, desde, actual, exito="Vínculo laboral guardado"):
                refrescar(); st.rerun()
        tabla(p["empresas"], {"empresa": "Empresa", "cargo": "Cargo", "desde": "Desde", "actual": "Actual"})
        if p["empresas"]:
            q = st.selectbox("Desvincular de", [e["empresa_id"] for e in p["empresas"]],
                             format_func=lambda i: next(e["empresa"] for e in p["empresas"] if e["empresa_id"] == i), key="v_emp_q")
            if st.button("Desvincular", key="v_emp_qbtn"):
                ejecutar(us.desvincular_empresa, uid, q, exito="Vínculo eliminado"); refrescar(); st.rerun()
        ver_cypher(us.Q_VINCULAR_EMPRESA, us.Q_DESVINCULAR_EMPRESA)

    with s[2]:
        c1, c2 = st.columns([2, 1])
        proy = c1.selectbox("Proyecto", list(opciones_proyectos()), format_func=lambda i: opciones_proyectos()[i], key="v_proy")
        rol = c2.text_input("Rol", "Colaborador", key="v_rol")
        if st.button("Agregar al proyecto", type="primary", key="v_proy_btn"):
            if ejecutar(us.vincular_proyecto, uid, proy, rol, exito="Participación registrada"):
                refrescar(); st.rerun()
        tabla(p["proyectos"], {"proyecto": "Proyecto", "rol": "Rol"})
        if p["proyectos"]:
            q = st.selectbox("Retirar del proyecto", [x["proyecto_id"] for x in p["proyectos"]],
                             format_func=lambda i: next(x["proyecto"] for x in p["proyectos"] if x["proyecto_id"] == i), key="v_proy_q")
            if st.button("Retirar", key="v_proy_qbtn"):
                ejecutar(us.desvincular_proyecto, uid, q, exito="Participación eliminada"); refrescar(); st.rerun()
        ver_cypher(us.Q_VINCULAR_PROYECTO, us.Q_DESVINCULAR_PROYECTO)

    with s[3]:
        conectados = {c["id"] for c in p["conexiones"]}
        candidatos = {k: v for k, v in opciones_usuarios().items() if k != uid and k not in conectados}
        otro = st.selectbox("Conectar con", list(candidatos), format_func=lambda i: candidatos[i], key="v_con")
        if st.button("Crear conexión profesional", type="primary", key="v_con_btn") and otro:
            r = ejecutar(us.conectar, uid, otro)
            if r:
                st.toast(f'{r["origen"]} ↔ {r["destino"]}', icon=":material/link:"); refrescar(); st.rerun()
            elif r is None:
                st.info("Ya estaban conectados.")
        tabla(p["conexiones"], {"nombre": "Contacto", "titular": "Titular"})
        if p["conexiones"]:
            q = st.selectbox("Eliminar conexión con", [c["id"] for c in p["conexiones"]],
                             format_func=lambda i: next(c["nombre"] for c in p["conexiones"] if c["id"] == i), key="v_con_q")
            if st.button("Eliminar conexión", key="v_con_qbtn"):
                ejecutar(us.desconectar, uid, q, exito="Conexión eliminada"); refrescar(); st.rerun()
        ver_cypher(us.Q_CONECTAR, us.Q_DESCONECTAR)
