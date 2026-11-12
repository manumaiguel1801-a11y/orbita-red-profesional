"""Pruebas de autenticación, validaciones, roles, permisos e invitaciones (contra Neo4j real)."""
import pytest

from orbita import catalogo as cat
from orbita import datos_demo, esquema, seguridad
from orbita import usuarios as us
from orbita.db import escribir, leer

PWD = "Clave#Segura9"


def _registro(n=1, **extra):
    datos = {"nombre": "TEST-Persona " + ["Cero", "Uno", "Dos", "Tres"][n], "email": f"test-sec{n}@ejemplo.test", "password": PWD,
             "confirmacion": PWD, "acepta_terminos": True, "titular": "QA", **extra}
    return seguridad.registrar(datos)


# ------------------------------------------------------------------ Contraseñas y validaciones (sin base)
def test_hash_y_verificacion():
    h = seguridad.hash_password("Abc123!x")
    assert h.startswith("pbkdf2_sha256$260000$") and "Abc123!x" not in h
    assert seguridad.verificar_password("Abc123!x", h)
    assert not seguridad.verificar_password("abc123!x", h)
    assert seguridad.hash_password("Abc123!x") != h          # sal aleatoria
    assert not seguridad.verificar_password("x", None) and not seguridad.verificar_password("x", "basura")


@pytest.mark.parametrize("pwd,falta", [("Ab1!", "al menos 8 caracteres"), ("abcdefg1!", "una letra mayúscula"),
                                       ("ABCDEFG1!", "una letra minúscula"), ("Abcdefgh!", "un número"),
                                       ("Abcdefgh1", "un símbolo (ej.: ! * # $)")])
def test_politica_password(pwd, falta):
    assert falta in seguridad.validar_password(pwd)


def test_password_no_contiene_correo_ni_nombre():
    assert "no contener su correo" in seguridad.validar_password("Carlos#2024x", "carlos@x.com")
    assert "no contener su nombre" in seguridad.validar_password("Martinez#99", "a@b.co", "Ana Martinez")
    assert seguridad.validar_password(PWD, "otro@x.com", "Ana Pérez") == []


@pytest.mark.parametrize("email,ok", [("ana@dominio.com", True), ("ANA@Dominio.CO", True), ("ana@", False),
                                      ("ana.dominio.com", False), ("", False), ("a b@x.com", False)])
def test_validar_email(email, ok):
    assert (seguridad.validar_email(email) is None) == ok


@pytest.mark.parametrize("nombre,ok", [("Ana Pérez", True), ("María José O'Neill", True), ("Ana", False),
                                       ("A", False), ("Ana 123", False), ("<script> x", False)])
def test_validar_nombre(nombre, ok):
    assert (seguridad.validar_nombre(nombre) is None) == ok


def test_validar_perfil():
    e = seguridad.validar_perfil({"nombre": "Ana Pérez", "email": "ana@x.co", "telefono": "abc", "anios_experiencia": 80})
    assert set(e) == {"telefono", "anios_experiencia"}


# ------------------------------------------------------------------ Registro
def test_registro_exitoso_y_sin_datos_sensibles(limpio):
    u = _registro(1, email="TEST-SEC1@Ejemplo.TEST")
    assert u["rol"] == "profesional" and u["email"] == "test-sec1@ejemplo.test"
    fila = leer("MATCH (u:Usuario {id: $id}) RETURN u.password_hash AS h, u.activo AS a", id=u["id"])[0]
    assert fila["h"].startswith("pbkdf2_sha256$") and fila["a"] is True
    perfil = us.obtener_usuario(u["id"])["usuario"]
    assert "password_hash" not in perfil and "sesion_hash" not in perfil


def test_registro_rechaza_datos_invalidos(limpio):
    _registro(1)
    with pytest.raises(ValueError) as e:
        seguridad.registrar({"nombre": "X", "email": "test-sec1@ejemplo.test", "password": "corta",
                             "confirmacion": "otra", "acepta_terminos": False})
    errores = e.value.args[0]
    assert set(errores) == {"nombre", "email", "password", "confirmacion", "acepta_terminos"}
    assert "Ya existe una cuenta" in errores["email"]


# ------------------------------------------------------------------ Inicio de sesión, sesiones y bloqueo
def test_login_sesion_y_logout(limpio):
    _registro(1)
    u, token = seguridad.iniciar_sesion(" Test-Sec1@ejemplo.test ", PWD)
    assert u["nombre"] == "TEST-Persona Uno" and len(token) >= 40
    assert seguridad.validar_sesion(token)["id"] == u["id"]
    assert leer("MATCH (u:Usuario {id:$id}) RETURN u.sesion_hash AS h", id=u["id"])[0]["h"] != token  # solo el hash
    assert seguridad.validar_sesion("token-falso") is None
    seguridad.cerrar_sesion(u["id"])
    assert seguridad.validar_sesion(token) is None


def test_login_mensajes_genericos(limpio):
    _registro(1)
    for email, pwd in [("test-sec1@ejemplo.test", "Incorrecta#1"), ("no-existe@ejemplo.test", PWD)]:
        with pytest.raises(seguridad.AutenticacionError, match="Correo o contraseña incorrectos"):
            seguridad.iniciar_sesion(email, pwd)
    with pytest.raises(seguridad.AutenticacionError, match="Ingrese su correo"):
        seguridad.iniciar_sesion("", "")


def test_bloqueo_tras_5_intentos(limpio):
    _registro(1)
    for _ in range(4):
        with pytest.raises(seguridad.AutenticacionError):
            seguridad.iniciar_sesion("test-sec1@ejemplo.test", "Mala#Clave1")
    with pytest.raises(seguridad.AutenticacionError, match="bloqueó"):
        seguridad.iniciar_sesion("test-sec1@ejemplo.test", "Mala#Clave1")
    with pytest.raises(seguridad.AutenticacionError, match="bloqueada temporalmente"):
        seguridad.iniciar_sesion("test-sec1@ejemplo.test", PWD)      # ni con la correcta
    escribir("MATCH (u:Usuario {email:'test-sec1@ejemplo.test'}) SET u.bloqueado_hasta = datetime() - duration('PT1S')")
    assert seguridad.iniciar_sesion("test-sec1@ejemplo.test", PWD)[0]   # al expirar, vuelve a funcionar


def test_cuenta_desactivada_y_sin_password(limpio):
    u = _registro(1)
    escribir("MATCH (u:Usuario {id:$id}) SET u.activo = false", id=u["id"])
    with pytest.raises(seguridad.AutenticacionError, match="desactivada"):
        seguridad.iniciar_sesion("test-sec1@ejemplo.test", PWD)
    us.crear_usuario({"nombre": "TEST-Sin Clave", "email": "test-sinclave@ejemplo.test"}, id="TEST-U50")
    with pytest.raises(seguridad.AutenticacionError, match="no tiene contraseña"):
        seguridad.iniciar_sesion("test-sinclave@ejemplo.test", PWD)


def test_cambiar_password(limpio):
    u = _registro(1)
    _, token = seguridad.iniciar_sesion("test-sec1@ejemplo.test", PWD)
    with pytest.raises(ValueError, match="actual no es correcta"):
        seguridad.cambiar_password(u["id"], "Otra#Clave1", "Nueva#Clave22", "Nueva#Clave22")
    with pytest.raises(ValueError, match="no coinciden"):
        seguridad.cambiar_password(u["id"], PWD, "Nueva#Clave22", "Nueva#Clave23")
    with pytest.raises(ValueError, match="distinta"):
        seguridad.cambiar_password(u["id"], PWD, PWD, PWD)
    with pytest.raises(ValueError, match="debe tener"):
        seguridad.cambiar_password(u["id"], PWD, "debil", "debil")
    seguridad.cambiar_password(u["id"], PWD, "Nueva#Clave22", "Nueva#Clave22")
    assert seguridad.validar_sesion(token) is None                  # cierra sesiones abiertas
    assert seguridad.iniciar_sesion("test-sec1@ejemplo.test", "Nueva#Clave22")[0]["id"] == u["id"]


def test_email_unico_al_editar_perfil(limpio):
    a, b = _registro(1), _registro(2)
    with pytest.raises(ValueError, match="otra cuenta"):
        us.actualizar_usuario(b["id"], {"email": a["email"]})


# ------------------------------------------------------------------ Roles y administración
def test_roles_y_permisos_admin(limpio):
    admin = seguridad.crear_admin("TEST-Admin Pruebas", "test-admin@ejemplo.test", PWD)
    u = _registro(1)
    with pytest.raises(PermissionError):
        seguridad.cambiar_rol(u["id"], u["id"], "admin")             # un profesional no puede auto-ascenderse
    assert seguridad.cambiar_rol(admin["id"], u["id"], "reclutador") == "reclutador"
    with pytest.raises(ValueError):
        seguridad.cambiar_rol(admin["id"], u["id"], "superusuario")
    with pytest.raises(ValueError):
        seguridad.activar_cuenta(admin["id"], admin["id"], False)    # no puede desactivarse a sí mismo
    assert seguridad.activar_cuenta(admin["id"], u["id"], False) is False
    assert seguridad.activar_cuenta(admin["id"], u["id"], True) is True
    assert seguridad.fijar_password_temporal(admin["id"], u["id"], "Temporal#2026")
    assert seguridad.iniciar_sesion("test-sec1@ejemplo.test", "Temporal#2026")[0]["rol"] == "reclutador"


def test_ultimo_admin_no_puede_degradarse(limpio):
    n_admins = leer(seguridad.Q_CONTAR_ADMINS)[0]["n"]
    admin = seguridad.crear_admin("TEST-Admin Pruebas", "test-admin@ejemplo.test", PWD)
    if n_admins == 0:   # solo es verificable si el admin de prueba es el único
        with pytest.raises(ValueError, match="único administrador"):
            seguridad.cambiar_rol(admin["id"], admin["id"], "profesional")


def test_permisos_de_reclutador(limpio):
    admin = seguridad.crear_admin("TEST-Admin Pruebas", "test-admin@ejemplo.test", PWD)
    rec, prof = _registro(1), _registro(2)
    seguridad.cambiar_rol(admin["id"], rec["id"], "reclutador")
    cat.crear_empresa({"nombre": "TEST-Empresa Propia"}, id="TEST-E1")
    cat.crear_empresa({"nombre": "TEST-Empresa Ajena"}, id="TEST-E2")
    us.vincular_empresa(rec["id"], "TEST-E1", "Talento", 2024, True)
    req = [{"habilidad": "TEST-Hab", "nivel_minimo": 3, "obligatoria": True}]
    o = cat.publicar_oferta_como(rec["id"], "TEST-E1", {"titulo": "TEST-Oferta propia"}, req)
    with pytest.raises(PermissionError):
        cat.publicar_oferta_como(rec["id"], "TEST-E2", {"titulo": "TEST-Ajena"}, req)   # otra empresa
    with pytest.raises(PermissionError):
        cat.publicar_oferta_como(prof["id"], "TEST-E1", {"titulo": "TEST-X"}, req)       # rol profesional
    with pytest.raises(ValueError, match="al menos una habilidad"):
        cat.publicar_oferta_como(rec["id"], "TEST-E1", {"titulo": "TEST-Sin requisitos"}, [])
    with pytest.raises(ValueError, match="título"):
        cat.publicar_oferta_como(rec["id"], "TEST-E1", {"titulo": "ab"}, req)
    otra = cat.crear_oferta("TEST-E2", {"titulo": "TEST-Oferta ajena"}, req)
    with pytest.raises(PermissionError):
        cat.eliminar_oferta_como(rec["id"], otra["id"])
    us.postular(prof["id"], o["id"])
    cat.estado_postulacion_como(rec["id"], o["id"], prof["id"], "Entrevista")
    assert cat.postulantes(o["id"])[0]["estado"] == "Entrevista"
    with pytest.raises(PermissionError):
        cat.estado_postulacion_como(prof["id"], o["id"], prof["id"], "Oferta")          # el postulante no puede
    us.vincular_empresa(rec["id"], "TEST-E1", "Talento", 2024, False)                   # deja la empresa
    assert not cat.puede_gestionar_oferta(rec["id"], o["id"])
    assert cat.puede_gestionar_oferta(admin["id"], otra["id"])                          # admin: cualquiera


# ------------------------------------------------------------------ Invitaciones de conexión
def test_invitaciones(limpio):
    a, b, c = _registro(1), _registro(2), _registro(3)
    assert us.enviar_invitacion(a["id"], b["id"]) == "enviada"
    assert us.enviar_invitacion(a["id"], b["id"]) == "enviada"          # idempotente
    assert len(us.invitaciones_enviadas(a["id"])) == 1
    assert [i["id"] for i in us.invitaciones_recibidas(b["id"])] == [a["id"]]
    assert us.aceptar_invitacion(b["id"], a["id"])
    assert us.enviar_invitacion(b["id"], a["id"]) == "ya_conectados"
    assert not us.invitaciones_recibidas(b["id"])
    us.enviar_invitacion(c["id"], a["id"])
    assert us.enviar_invitacion(a["id"], c["id"]) == "conectados"       # invitación cruzada = conexión
    us.enviar_invitacion(b["id"], c["id"])
    assert us.rechazar_invitacion(c["id"], b["id"]) == 1
    us.enviar_invitacion(b["id"], c["id"])
    assert us.cancelar_invitacion(b["id"], c["id"]) == 1
    with pytest.raises(ValueError):
        us.enviar_invitacion(a["id"], a["id"])


# ------------------------------------------------------------------ Datos de demostración
def test_borrar_solo_datos_demo(limpio):
    lote = "TEST-lote"
    escribir("""CREATE (:Usuario {id:'TEST-D1', nombre:'TEST-Demo Uno', email:'test-d1@ejemplo.test', demo:$l})
                 -[:TIENE_HABILIDAD {nivel:3}]->(h:Habilidad {nombre:'TEST-HabUsada', demo:$l}),
                (:Habilidad {nombre:'TEST-HabLibre', demo:$l}),
                (:Usuario {id:'TEST-R1', nombre:'TEST-Real Uno', email:'test-r1@ejemplo.test'})-[:TIENE_HABILIDAD {nivel:4}]->(h)""", l=lote)
    with pytest.raises(PermissionError):
        esquema.borrar_datos_demo("borrar", lote)
    r = esquema.borrar_datos_demo("BORRAR DEMO", lote)
    assert r == {"eliminados": 2, "conservados": 1}
    quedan = {x["n"]: x["d"] for x in leer("MATCH (n) WHERE n.nombre STARTS WITH 'TEST-' RETURN n.nombre AS n, n.demo AS d")}
    assert quedan == {"TEST-HabUsada": None, "TEST-Real Uno": None}    # lo real y lo que usa, intactos y sin marca


def test_conexiones_demo_coinciden_con_el_generador():
    """Regresión: la carga debe producir exactamente las conexiones definidas (semilla 42)."""
    esperadas = {(c["a"], c["b"]) for c in datos_demo.construir()["conexiones"]}
    reales = {(r["a"], r["b"]) for r in leer("""
        MATCH (a:Usuario)-[:CONECTA_CON]-(b:Usuario)
        WHERE a.id < b.id AND a.demo IS NOT NULL AND b.demo IS NOT NULL AND a.id STARTS WITH 'U0'
        RETURN a.id AS a, b.id AS b""")}
    assert esperadas <= reales
    assert len(esperadas) == 84


def test_cuentas_demo_tienen_password_y_rol():
    """Se verifica sin iniciar sesión, para no cerrar una sesión abierta en el navegador con esa cuenta."""
    r = leer("MATCH (u:Usuario {email: 'camila.herrera@ejemplo.com'}) RETURN u.password_hash AS h, u.rol AS rol")[0]
    assert r["rol"] == "reclutador" and seguridad.verificar_password(datos_demo.PASSWORD_DEMO, r["h"])
    roles = {x["rol"] for x in leer("MATCH (u:Usuario) WHERE u.demo IS NOT NULL RETURN DISTINCT u.rol AS rol")}
    assert roles == {"profesional", "reclutador"}
