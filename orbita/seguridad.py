"""Autenticación, sesiones, roles y validaciones.

- Contraseñas: PBKDF2-HMAC-SHA256 con sal aleatoria de 16 bytes y 260 000 iteraciones
  (biblioteca estándar `hashlib`). Nunca se guarda la contraseña en texto plano.
- Inicio de sesión con mensaje genérico (no revela si el correo existe) y bloqueo temporal
  de 5 minutos tras 5 intentos fallidos consecutivos (estado guardado en Neo4j).
- Sesiones: token aleatorio de 256 bits; en Neo4j solo se guarda su hash SHA-256 y la expiración (8 h).
- Roles: profesional, reclutador, admin. Los permisos se verifican en el servidor (Cypher), no solo en la interfaz.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import re
import secrets

from neo4j.exceptions import ConstraintError

from .db import escribir, leer
from .usuarios import nuevo_id

ITERACIONES = 260_000
MAX_INTENTOS = 5
MINUTOS_BLOQUEO = 5
HORAS_SESION = 8
ROLES = {"profesional": "Profesional", "reclutador": "Reclutador", "admin": "Administrador"}
CAMPOS_SENSIBLES = {"password_hash", "sesion_hash", "sesion_expira", "intentos_fallidos", "bloqueado_hasta"}

RE_EMAIL = re.compile(r"^[a-z0-9._%+\-]+@[a-z0-9.\-]+\.[a-z]{2,}$")
RE_NOMBRE = re.compile(r"^[A-Za-zÁÉÍÓÚÜÑáéíóúüñ' .\-]{2,80}$")
RE_TELEFONO = re.compile(r"^\+?[0-9 ()\-]{7,20}$")


class AutenticacionError(Exception):
    """Error de inicio de sesión con mensaje apto para mostrar al usuario."""


# ================================================================ Contraseñas
def hash_password(password: str, sal: bytes | None = None) -> str:
    sal = sal or secrets.token_bytes(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), sal, ITERACIONES)
    return f"pbkdf2_sha256${ITERACIONES}${base64.b64encode(sal).decode()}${base64.b64encode(dk).decode()}"


def verificar_password(password: str, almacenado: str | None) -> bool:
    if not almacenado:
        return False
    try:
        _, it, sal, dk = almacenado.split("$")
        calc = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), base64.b64decode(sal), int(it))
        return hmac.compare_digest(calc, base64.b64decode(dk))
    except (ValueError, TypeError):
        return False


_HASH_SEÑUELO = hash_password("señuelo-para-igualar-tiempos")


# ================================================================ Validaciones
def validar_email(email: str) -> str | None:
    email = (email or "").strip().lower()
    if not email:
        return "El correo es obligatorio."
    if len(email) > 120 or not RE_EMAIL.match(email):
        return "Ingrese un correo válido (ej.: nombre@dominio.com)."
    return None


def validar_nombre(nombre: str) -> str | None:
    nombre = (nombre or "").strip()
    if not nombre:
        return "El nombre es obligatorio."
    if not RE_NOMBRE.match(nombre):
        return "Use entre 2 y 80 caracteres: solo letras, espacios, apóstrofos, puntos o guiones."
    if len(nombre.split()) < 2:
        return "Ingrese nombre y apellido."
    return None


def validar_password(password: str, email: str = "", nombre: str = "") -> list[str]:
    errores = []
    p = password or ""
    if len(p) < 8:
        errores.append("al menos 8 caracteres")
    if len(p) > 128:
        errores.append("máximo 128 caracteres")
    if not re.search(r"[A-ZÁÉÍÓÚÑ]", p):
        errores.append("una letra mayúscula")
    if not re.search(r"[a-záéíóúñ]", p):
        errores.append("una letra minúscula")
    if not re.search(r"\d", p):
        errores.append("un número")
    if not re.search(r"[^A-Za-z0-9ÁÉÍÓÚÑáéíóúñ]", p):
        errores.append("un símbolo (ej.: ! * # $)")
    local = (email or "").split("@")[0].lower()
    if len(local) >= 4 and local in p.lower():
        errores.append("no contener su correo")
    if any(len(x) >= 4 and x.lower() in p.lower() for x in (nombre or "").split()):
        errores.append("no contener su nombre")
    return errores


def fuerza_password(password: str) -> tuple[int, str]:
    """0-4 y etiqueta, para el medidor visual."""
    p = password or ""
    puntos = sum([len(p) >= 8, len(p) >= 12, bool(re.search(r"[A-Z]", p) and re.search(r"[a-z]", p)),
                  bool(re.search(r"\d", p)), bool(re.search(r"[^A-Za-z0-9]", p))])
    nivel = min(4, max(0, puntos - 1)) if p else 0
    return nivel, ["Muy débil", "Débil", "Aceptable", "Fuerte", "Muy fuerte"][nivel]


def validar_perfil(datos: dict) -> dict[str, str]:
    """Valida los campos editables del perfil. Devuelve {campo: mensaje}."""
    e = {}
    if (m := validar_nombre(datos.get("nombre", ""))):
        e["nombre"] = m
    if (m := validar_email(datos.get("email", ""))):
        e["email"] = m
    tel = (datos.get("telefono") or "").strip()
    if tel and not RE_TELEFONO.match(tel):
        e["telefono"] = "Teléfono no válido (7-20 dígitos; puede usar +, espacios, guiones)."
    anios = datos.get("anios_experiencia")
    if anios not in (None, "") and not (0 <= int(anios) <= 60):
        e["anios_experiencia"] = "Los años de experiencia deben estar entre 0 y 60."
    for campo, maximo in (("titular", 120), ("ciudad", 60), ("resumen", 1000)):
        if len(datos.get(campo) or "") > maximo:
            e[campo] = f"Máximo {maximo} caracteres."
    return e


def validar_registro(datos: dict) -> dict[str, str]:
    e = {}
    if (m := validar_nombre(datos.get("nombre", ""))):
        e["nombre"] = m
    if (m := validar_email(datos.get("email", ""))):
        e["email"] = m
    elif email_registrado(datos["email"]):
        e["email"] = "Ya existe una cuenta con este correo. Inicie sesión o use otro correo."
    faltas = validar_password(datos.get("password", ""), datos.get("email", ""), datos.get("nombre", ""))
    if faltas:
        e["password"] = "La contraseña debe tener " + ", ".join(faltas) + "."
    if datos.get("password") != datos.get("confirmacion"):
        e["confirmacion"] = "Las contraseñas no coinciden."
    if not datos.get("acepta_terminos"):
        e["acepta_terminos"] = "Debe aceptar los términos de uso y el tratamiento de datos."
    if len(datos.get("titular") or "") > 120:
        e["titular"] = "Máximo 120 caracteres."
    return e


# ================================================================ Consultas
Q_EMAIL_EXISTE = "RETURN EXISTS { (:Usuario {email: $email}) } AS existe"

Q_REGISTRAR = """
CREATE (u:Usuario {id: $id, fecha_registro: date(), rol: 'profesional', activo: true,
                   password_hash: $hash, intentos_fallidos: 0})
SET u += $props
RETURN u.id AS id, u.nombre AS nombre, u.email AS email, u.rol AS rol
"""

Q_CREDENCIALES = """
MATCH (u:Usuario {email: $email})
RETURN u.id AS id, u.nombre AS nombre, u.email AS email, coalesce(u.rol, 'profesional') AS rol,
       u.password_hash AS hash, coalesce(u.activo, true) AS activo,
       coalesce(u.bloqueado_hasta > datetime(), false) AS bloqueado,
       CASE WHEN u.bloqueado_hasta > datetime()
            THEN duration.inSeconds(datetime(), u.bloqueado_hasta).seconds ELSE 0 END AS segundos_restantes
"""

Q_FALLO = """
MATCH (u:Usuario {id: $id})
SET u.intentos_fallidos = coalesce(u.intentos_fallidos, 0) + 1
WITH u, u.intentos_fallidos >= $max AS bloquear
FOREACH (_ IN CASE WHEN bloquear THEN [1] ELSE [] END |
  SET u.bloqueado_hasta = datetime() + duration({minutes: $minutos}), u.intentos_fallidos = 0)
RETURN bloquear, u.intentos_fallidos AS intentos
"""

Q_EXITO = """
MATCH (u:Usuario {id: $id})
SET u.intentos_fallidos = 0, u.bloqueado_hasta = null, u.ultimo_acceso = datetime(),
    u.sesion_hash = $sesion_hash, u.sesion_expira = datetime() + duration({hours: $horas})
"""

Q_VALIDAR_SESION = """
MATCH (u:Usuario {sesion_hash: $sesion_hash})
WHERE u.sesion_expira > datetime() AND coalesce(u.activo, true)
RETURN u.id AS id, u.nombre AS nombre, u.email AS email, coalesce(u.rol, 'profesional') AS rol
"""

Q_CERRAR_SESION = "MATCH (u:Usuario {id: $id}) REMOVE u.sesion_hash, u.sesion_expira"

Q_HASH_ACTUAL = "MATCH (u:Usuario {id: $id}) RETURN u.password_hash AS hash"

Q_FIJAR_PASSWORD = """
MATCH (u:Usuario {id: $id})
SET u.password_hash = $hash, u.intentos_fallidos = 0, u.bloqueado_hasta = null
REMOVE u.sesion_hash, u.sesion_expira
RETURN u.id AS id
"""

Q_ES_ADMIN = "MATCH (u:Usuario {id: $id}) RETURN coalesce(u.rol, '') = 'admin' AND coalesce(u.activo, true) AS es_admin"

Q_CAMBIAR_ROL = "MATCH (u:Usuario {id: $id}) SET u.rol = $rol RETURN u.rol AS rol"

Q_CONTAR_ADMINS = "MATCH (u:Usuario {rol: 'admin'}) WHERE coalesce(u.activo, true) RETURN count(u) AS n"

Q_ACTIVAR = """
MATCH (u:Usuario {id: $id}) SET u.activo = $activo
FOREACH (_ IN CASE WHEN $activo THEN [] ELSE [1] END | REMOVE u.sesion_hash, u.sesion_expira)
RETURN u.activo AS activo
"""


def email_registrado(email: str) -> bool:
    return leer(Q_EMAIL_EXISTE, email=(email or "").strip().lower())[0]["existe"]


def registrar(datos: dict) -> dict:
    """Crea una cuenta nueva (rol profesional). Lanza ValueError con {campo: mensaje} si no es válida."""
    errores = validar_registro(datos)
    if errores:
        raise ValueError(errores)
    props = {"nombre": " ".join(datos["nombre"].split()), "email": datos["email"].strip().lower()}
    for campo in ("titular", "ciudad"):
        if (datos.get(campo) or "").strip():
            props[campo] = datos[campo].strip()
    try:
        return escribir(Q_REGISTRAR, id=nuevo_id("U"), hash=hash_password(datos["password"]), props=props)[0]
    except ConstraintError:  # carrera: alguien registró el mismo correo entre la validación y la escritura
        raise ValueError({"email": "Ya existe una cuenta con este correo."})


def iniciar_sesion(email: str, password: str) -> tuple[dict, str]:
    """Devuelve (usuario, token_de_sesion). Lanza AutenticacionError con un mensaje seguro."""
    email = (email or "").strip().lower()
    if not email or not password:
        raise AutenticacionError("Ingrese su correo y su contraseña.")
    filas = leer(Q_CREDENCIALES, email=email)
    if not filas:
        verificar_password(password, _HASH_SEÑUELO)  # mismo tiempo de respuesta exista o no el correo
        raise AutenticacionError("Correo o contraseña incorrectos.")
    u = filas[0]
    if u["bloqueado"]:
        minutos = max(1, round(u["segundos_restantes"] / 60))
        raise AutenticacionError(f"Cuenta bloqueada temporalmente por intentos fallidos. Intente de nuevo en {minutos} min.")
    if not u["activo"]:
        raise AutenticacionError("Esta cuenta está desactivada. Contacte al administrador.")
    if not u["hash"]:
        raise AutenticacionError("Esta cuenta aún no tiene contraseña. Solicite al administrador una contraseña temporal.")
    if not verificar_password(password, u["hash"]):
        r = escribir(Q_FALLO, id=u["id"], max=MAX_INTENTOS, minutos=MINUTOS_BLOQUEO)[0]
        if r["bloquear"]:
            raise AutenticacionError(f"Demasiados intentos fallidos. La cuenta se bloqueó durante {MINUTOS_BLOQUEO} minutos.")
        restantes = MAX_INTENTOS - r["intentos"]
        raise AutenticacionError("Correo o contraseña incorrectos."
                                 + (f" Le quedan {restantes} intentos." if restantes <= 2 else ""))
    token = secrets.token_urlsafe(32)
    escribir(Q_EXITO, id=u["id"], sesion_hash=_hash_token(token), horas=HORAS_SESION)
    return {k: u[k] for k in ("id", "nombre", "email", "rol")}, token


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def validar_sesion(token: str | None) -> dict | None:
    if not token or len(token) > 100:
        return None
    r = leer(Q_VALIDAR_SESION, sesion_hash=_hash_token(token))
    return r[0] if r else None


def cerrar_sesion(usuario_id: str) -> None:
    escribir(Q_CERRAR_SESION, id=usuario_id)


def cambiar_password(usuario_id: str, actual: str, nueva: str, confirmacion: str, email: str = "", nombre: str = "") -> None:
    if not verificar_password(actual or "", leer(Q_HASH_ACTUAL, id=usuario_id)[0]["hash"]):
        raise ValueError("La contraseña actual no es correcta.")
    if nueva != confirmacion:
        raise ValueError("La nueva contraseña y su confirmación no coinciden.")
    if nueva == actual:
        raise ValueError("La nueva contraseña debe ser distinta de la actual.")
    faltas = validar_password(nueva, email, nombre)
    if faltas:
        raise ValueError("La nueva contraseña debe tener " + ", ".join(faltas) + ".")
    escribir(Q_FIJAR_PASSWORD, id=usuario_id, hash=hash_password(nueva))


def verificar_password_usuario(usuario_id: str, password: str) -> bool:
    r = leer(Q_HASH_ACTUAL, id=usuario_id)
    return bool(r) and verificar_password(password or "", r[0]["hash"])


# ================================================================ Administración de cuentas
def es_admin(usuario_id: str) -> bool:
    r = leer(Q_ES_ADMIN, id=usuario_id)
    return bool(r) and r[0]["es_admin"]


def _exigir_admin(actor_id: str) -> None:
    if not es_admin(actor_id):
        raise PermissionError("Solo un administrador puede realizar esta acción.")


def cambiar_rol(actor_id: str, usuario_id: str, rol: str) -> str:
    _exigir_admin(actor_id)
    if rol not in ROLES:
        raise ValueError("Rol no válido.")
    if actor_id == usuario_id and rol != "admin" and leer(Q_CONTAR_ADMINS)[0]["n"] <= 1:
        raise ValueError("No puede quitarse el rol de administrador: es el único administrador activo.")
    return escribir(Q_CAMBIAR_ROL, id=usuario_id, rol=rol)[0]["rol"]


def activar_cuenta(actor_id: str, usuario_id: str, activo: bool) -> bool:
    _exigir_admin(actor_id)
    if actor_id == usuario_id and not activo:
        raise ValueError("No puede desactivar su propia cuenta.")
    return escribir(Q_ACTIVAR, id=usuario_id, activo=bool(activo))[0]["activo"]


def fijar_password_temporal(actor_id: str, usuario_id: str, nueva: str) -> bool:
    _exigir_admin(actor_id)
    faltas = validar_password(nueva)
    if faltas:
        raise ValueError("La contraseña temporal debe tener " + ", ".join(faltas) + ".")
    return bool(escribir(Q_FIJAR_PASSWORD, id=usuario_id, hash=hash_password(nueva)))


def crear_admin(nombre: str, email: str, password: str) -> dict:
    """Usado por scripts/crear_admin.py. Si el correo existe, lo promueve a admin y fija la contraseña."""
    if (m := validar_email(email)) or (m := validar_nombre(nombre)):
        raise ValueError(m)
    faltas = validar_password(password, email, nombre)
    if faltas:
        raise ValueError("La contraseña debe tener " + ", ".join(faltas) + ".")
    return escribir("""
        MERGE (u:Usuario {email: $email})
          ON CREATE SET u.id = $id, u.nombre = $nombre, u.fecha_registro = date(), u.titular = 'Administrador de la plataforma'
        SET u.rol = 'admin', u.activo = true, u.password_hash = $hash, u.intentos_fallidos = 0, u.bloqueado_hasta = null
        RETURN u.id AS id, u.nombre AS nombre, u.email AS email, u.rol AS rol
    """, email=email.strip().lower(), id=nuevo_id("U"), nombre=" ".join(nombre.split()), hash=hash_password(password))[0]


def publico(d: dict | None) -> dict | None:
    """Elimina campos sensibles antes de enviar datos a la interfaz."""
    return None if d is None else {k: v for k, v in d.items() if k not in CAMPOS_SENSIBLES}
