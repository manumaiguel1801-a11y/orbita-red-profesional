"""Pantalla pública: iniciar sesión y crear cuenta."""
import streamlit as st

from orbita import analitica, seguridad
from orbita.datos_demo import PASSWORD_DEMO
from ui import estilo, sesion
from ui.estilo import esc, icono

LOGO_MARCA = """<svg width="44" height="44" viewBox="0 0 48 48" aria-hidden="true">
  <defs><linearGradient id="om" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#C4B5FD"/><stop offset="1" stop-color="#8B5CF6"/></linearGradient></defs>
  <rect x="2" y="2" width="44" height="44" rx="13" fill="rgba(255,255,255,.08)" stroke="rgba(255,255,255,.25)"/>
  <circle cx="24" cy="24" r="7" fill="url(#om)"/>
  <ellipse cx="24" cy="24" rx="17" ry="7" fill="none" stroke="#A3E635" stroke-width="2" transform="rotate(-28 24 24)"/>
  <circle cx="38" cy="16.5" r="3" fill="#A3E635"/>
</svg>"""


def _error(campo: str) -> None:
    msg = st.session_state.get("errores_registro", {}).get(campo)
    if msg:
        st.markdown(f'<div class="ox-err">{icono("alerta", 14)}{esc(msg)}</div>', unsafe_allow_html=True)


def _medidor(password: str) -> None:
    if not password:
        return
    nivel, texto = seguridad.fuerza_password(password)
    colores = ["#F87171", "#FB923C", "#FACC15", "#A3E635", "#84CC16"]
    barras = "".join(f'<i style="background:{colores[nivel] if i <= nivel else "#27272A"}"></i>' for i in range(5))
    faltas = seguridad.validar_password(password, st.session_state.get("reg_email", ""), st.session_state.get("reg_nombre", ""))
    detalle = ("Falta: " + ", ".join(faltas)) if faltas else "Cumple todos los requisitos"
    st.markdown(f'<div class="ox-fuerza">{barras}</div><div style="font-size:.76rem;color:{colores[nivel]};margin-bottom:.5rem">'
                f'<b>{texto}</b> · <span style="color:#A1A1AA">{esc(detalle)}</span></div>', unsafe_allow_html=True)


def _hero():
    try:
        r = analitica.resumen()
    except Exception:  # noqa: BLE001
        r = {"usuarios": "—", "ofertas_activas": "—", "conexiones": "—"}
    item = lambda ic, t, d: (f'<div class="it"><div class="b">{icono(ic, 19)}</div><div><b>{t}</b><span>{d}</span></div></div>')  # noqa: E731
    estilo.html(f"""
    <div class="ox-auth">
      <div class="ox-sistema"><div class="o"></div><div class="o"></div><div class="o"></div><div class="n"></div></div>
      <div class="ox-marca">{LOGO_MARCA}<b>Órbita</b></div>
      <h1>Todo tu universo profesional, <em>en órbita.</em></h1>
      <p>Descubre a quién conoces, a quién deberías conocer y qué oportunidades giran a pocos pasos de ti.</p>
      {item("conexion", "Conexiones con contexto", "Contactos en común y la ruta más corta hacia cualquier empresa.")}
      {item("chispa", "Recomendaciones explicables", "Empleos y personas según tus habilidades y tu red, con su puntaje.")}
      {item("objetivo", "Para reclutadores", "Publica vacantes y encuentra candidatos por competencias y cercanía.")}
      <div class="stats"><div><b>{r['usuarios']}</b><span>profesionales</span></div>
        <div><b>{r['ofertas_activas']}</b><span>ofertas activas</span></div>
        <div><b>{r['conexiones']}</b><span>conexiones</span></div></div>
    </div>""")


def _login():
    estilo.html('<div class="ox-auth-t">Bienvenido de nuevo</div><div class="ox-auth-s">Ingrese con su correo y contraseña.</div>')
    with st.form("form_login", border=False):
        email = st.text_input("Correo electrónico", placeholder="nombre@dominio.com", key="login_email")
        password = st.text_input("Contraseña", type="password", key="login_password")
        enviar = st.form_submit_button("Iniciar sesión", type="primary", use_container_width=True)
    if enviar:
        try:
            u, token = seguridad.iniciar_sesion(email, password)
        except seguridad.AutenticacionError as e:
            st.error(str(e), icon=":material/error:")
        else:
            sesion.iniciar(u, token)
            st.session_state["bienvenida"] = f"Hola, {u['nombre'].split()[0]}"
            st.rerun()
    with st.expander("Cuentas de demostración", icon=":material/science:"):
        st.caption("Cuentas ficticias incluidas con los datos de demostración. Todas usan la misma contraseña.")
        st.markdown(f"""
| Rol | Correo |
|---|---|
| Profesional | `valentina.rojas@ejemplo.com` |
| Profesional (sin conexiones) | `elena.rios@ejemplo.com` |
| Reclutadora · Cumbre Talento | `camila.herrera@ejemplo.com` |
| Reclutadora · Andina Analytics | `daniela.vargas@ejemplo.com` |

Contraseña: `{PASSWORD_DEMO}` · El administrador se crea con `python scripts/crear_admin.py`.""")


def _registro():
    estilo.html('<div class="ox-auth-t">Crear una cuenta</div><div class="ox-auth-s">Entra en órbita en menos de un minuto.</div>')
    c1, c2 = st.columns(2)
    with c1:
        st.text_input("Nombre y apellido *", key="reg_nombre", placeholder="Ana María Pérez")
        _error("nombre")
    with c2:
        st.text_input("Correo electrónico *", key="reg_email", placeholder="ana@dominio.com")
        _error("email")
    c1, c2 = st.columns(2)
    with c1:
        st.text_input("Titular profesional", key="reg_titular", placeholder="Ej.: Ingeniera de Datos")
        _error("titular")
    with c2:
        st.text_input("Ciudad", key="reg_ciudad", placeholder="Ej.: Bogotá")
    st.text_input("Contraseña *", type="password", key="reg_password",
                  help="Mínimo 8 caracteres con mayúscula, minúscula, número y símbolo.")
    _medidor(st.session_state.get("reg_password", ""))
    _error("password")
    st.text_input("Confirmar contraseña *", type="password", key="reg_confirmacion")
    _error("confirmacion")
    st.checkbox("Acepto los términos de uso y el tratamiento de mis datos personales.", key="reg_terminos")
    _error("acepta_terminos")
    if st.button("Crear cuenta", type="primary", use_container_width=True, key="reg_btn"):
        datos = {"nombre": st.session_state.reg_nombre, "email": st.session_state.reg_email,
                 "titular": st.session_state.reg_titular, "ciudad": st.session_state.reg_ciudad,
                 "password": st.session_state.reg_password, "confirmacion": st.session_state.reg_confirmacion,
                 "acepta_terminos": st.session_state.reg_terminos}
        try:
            seguridad.registrar(datos)
        except ValueError as e:
            st.session_state["errores_registro"] = e.args[0] if isinstance(e.args[0], dict) else {"email": str(e)}
            st.rerun()
        st.session_state.pop("errores_registro", None)
        u, token = seguridad.iniciar_sesion(datos["email"], datos["password"])
        sesion.iniciar(u, token)
        st.session_state["bienvenida"] = f"Bienvenido/a a Órbita, {u['nombre'].split()[0]}. Completa tu perfil para recibir mejores recomendaciones."
        st.session_state["ir_a_perfil"] = True
        st.rerun()
    if st.session_state.get("errores_registro"):
        st.error("Revise los campos marcados.", icon=":material/error:")


def pagina():
    estilo.aplicar_auth()
    if (aviso := st.session_state.pop("aviso_sesion", None)):
        st.warning(aviso, icon=":material/info:")
    izq, der = st.columns([1.08, 1], gap="large")
    with izq:
        _hero()
    with der:
        st.write("")
        with st.container(border=True):
            t = st.tabs(["Iniciar sesión", "Crear cuenta"])
            with t[0]:
                _login()
            with t[1]:
                _registro()
        estilo.html(f'<div class="ox-nota">{icono("candado", 15)}<span>Tras 5 intentos fallidos, la cuenta se bloquea durante 5 minutos.</span></div>')
