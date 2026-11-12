"""Pruebas de la interfaz contra Neo4j real: cada página con el rol que le corresponde,
registro e inicio de sesión de punta a punta desde los formularios."""
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from orbita import catalogo as cat
from orbita import seguridad
from orbita import usuarios as us
from orbita.db import leer

RAIZ = str(Path(__file__).resolve().parent.parent)
PWD = "Clave#Segura9"

PLANTILLA = """
import sys
sys.path.insert(0, {raiz!r})
import importlib
import streamlit as st
from ui import estilo
estilo.aplicar()
usuario = {usuario!r}
if usuario:
    st.session_state["usuario"] = usuario
getattr(importlib.import_module({modulo!r}), {funcion!r})()
"""


def correr(modulo, funcion, usuario=None):
    at = AppTest.from_string(PLANTILLA.format(raiz=RAIZ, modulo=modulo, funcion=funcion, usuario=usuario), default_timeout=180)
    at.run()
    return at


def sin_errores(at):
    assert not at.exception, [e.message for e in at.exception]
    assert not at.error, [e.value for e in at.error]


@pytest.fixture()
def cuentas(limpio):
    admin = seguridad.crear_admin("TEST-Admin Pruebas", "test-admin@ejemplo.test", PWD)
    datos = {"password": PWD, "confirmacion": PWD, "acepta_terminos": True}
    prof = seguridad.registrar({"nombre": "TEST-Pro Uno", "email": "test-pro@ejemplo.test", **datos})
    rec = seguridad.registrar({"nombre": "TEST-Reclu Uno", "email": "test-rec@ejemplo.test", **datos})
    seguridad.cambiar_rol(admin["id"], rec["id"], "reclutador")
    cat.crear_empresa({"nombre": "TEST-Empresa UI"}, id="TEST-E1")
    us.vincular_empresa(rec["id"], "TEST-E1", "Talento", 2024, True)
    cat.publicar_oferta_como(rec["id"], "TEST-E1", {"titulo": "TEST-Oferta UI"}, [{"habilidad": "Python", "nivel_minimo": 2, "obligatoria": True}])
    us.asignar_habilidad(prof["id"], "Python", 3)
    us.enviar_invitacion(rec["id"], prof["id"])
    sesion = lambda u, rol: {"id": u["id"], "nombre": u["nombre"], "email": u["email"], "rol": rol}  # noqa: E731
    return {"admin": sesion(admin, "admin"), "profesional": sesion(prof, "profesional"), "reclutador": sesion(rec, "reclutador")}


PAGINAS_PROFESIONAL = [("ui.inicio", "pagina"), ("ui.perfil_pg", "pagina"), ("ui.mi_red_pg", "pagina"), ("ui.empleos_pg", "pagina"),
                       ("ui.catalogo_pg", "pagina_proyectos"), ("ui.recomendaciones_pg", "pagina"), ("ui.red_pg", "pagina"),
                       ("ui.analitica_pg", "pagina"), ("ui.explorador_pg", "pagina")]
PAGINAS_RECLUTADOR = [("ui.inicio", "pagina"), ("ui.reclutador_pg", "pagina"), ("ui.recomendaciones_pg", "pagina")]
PAGINAS_ADMIN = [("ui.inicio", "pagina"), ("ui.usuarios_pg", "pagina"), ("ui.empresas_pg", "pagina"),
                 ("ui.catalogo_pg", "pagina_habilidades"), ("ui.catalogo_pg", "pagina_proyectos"), ("ui.admin_pg", "pagina"),
                 ("ui.reclutador_pg", "pagina"), ("ui.recomendaciones_pg", "pagina")]


def test_todas_las_paginas_por_rol(cuentas):
    for rol, paginas in (("profesional", PAGINAS_PROFESIONAL), ("reclutador", PAGINAS_RECLUTADOR), ("admin", PAGINAS_ADMIN)):
        for modulo, funcion in paginas:
            at = correr(modulo, funcion, cuentas[rol])
            assert not at.exception, (rol, modulo, [e.message for e in at.exception])
            assert not at.error, (rol, modulo, [e.value for e in at.error])


def test_pantalla_de_acceso_sin_sesion():
    at = correr("ui.auth_pg", "pagina")
    sin_errores(at)
    assert any("Bienvenido de nuevo" in m.value for m in at.markdown)


def test_app_sin_sesion_muestra_acceso():
    at = AppTest.from_file(str(Path(RAIZ) / "app.py"), default_timeout=180)
    at.run()
    assert not at.exception, [e.message for e in at.exception]
    assert any("Bienvenido de nuevo" in m.value for m in at.markdown)


def test_registro_desde_formulario_valida_y_crea_cuenta(limpio):
    at = correr("ui.auth_pg", "pagina")
    at.button(key="reg_btn").click().run()                       # todo vacío
    assert any("ox-err" in m.value for m in at.markdown)
    assert not leer("MATCH (u:Usuario) WHERE u.email STARTS WITH 'test-ui' RETURN u")
    at.text_input(key="reg_nombre").set_value("TEST-Ana Interfaz")
    at.text_input(key="reg_email").set_value("test-ui@ejemplo.test")
    at.text_input(key="reg_password").set_value(PWD)
    at.text_input(key="reg_confirmacion").set_value(PWD)
    at.checkbox(key="reg_terminos").check()
    at.button(key="reg_btn").click().run()
    assert not at.exception
    r = leer("MATCH (u:Usuario {email: 'test-ui@ejemplo.test'}) RETURN u.rol AS rol, u.sesion_hash IS NOT NULL AS sesion")
    assert r == [{"rol": "profesional", "sesion": True}]          # cuenta creada e iniciada
    assert at.session_state["usuario"]["email"] == "test-ui@ejemplo.test"


def test_login_desde_app_y_restauracion_por_url(cuentas):
    at = AppTest.from_file(str(Path(RAIZ) / "app.py"), default_timeout=180)
    at.run()
    at.text_input(key="login_email").set_value("test-pro@ejemplo.test")
    at.text_input(key="login_password").set_value("Incorrecta#1")
    at.button[0].click().run()
    assert any("incorrectos" in e.value for e in at.error)
    at.text_input(key="login_password").set_value(PWD)
    at.button[0].click().run()
    assert not at.exception, [e.message for e in at.exception]
    assert at.session_state["usuario"]["email"] == "test-pro@ejemplo.test"
    token = at.query_params["s"][0] if isinstance(at.query_params["s"], list) else at.query_params["s"]
    # Una pestaña nueva con el token en la URL restaura la sesión (simula recargar la página)
    nueva = AppTest.from_file(str(Path(RAIZ) / "app.py"), default_timeout=180)
    nueva.query_params["s"] = token
    nueva.run()
    assert not nueva.exception, [e.message for e in nueva.exception]
    assert nueva.session_state["usuario"]["id"] == cuentas["profesional"]["id"]


def test_admin_registra_usuario_con_password_temporal(cuentas):
    at = correr("ui.usuarios_pg", "pagina", cuentas["admin"])
    at.text_input(key="crear_nombre").set_value("TEST-Desde Interfaz")
    at.text_input(key="crear_email").set_value("test-ui2@ejemplo.test")
    at.text_input(key="crear_tmp").set_value("Temporal#2026")
    next(b for b in at.button if b.label == "Registrar profesional").click()
    at.run()
    assert not at.exception
    assert seguridad.iniciar_sesion("test-ui2@ejemplo.test", "Temporal#2026")[0]["nombre"] == "TEST-Desde Interfaz"


def test_profesional_no_ve_candidatos(cuentas):
    at = correr("ui.recomendaciones_pg", "pagina", cuentas["profesional"])
    assert any("reclutadores y administradores" in i.value for i in at.info)
