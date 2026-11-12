"""CRUD de usuarios y sus vínculos (habilidades, empresas, proyectos, conexiones, postulaciones)."""
from __future__ import annotations

import uuid
from datetime import date

from .db import leer, escribir

CAMPOS_USUARIO = ["nombre", "email", "titular", "ciudad", "telefono", "anios_experiencia", "resumen", "nivel_educativo"]

# ---------------------------------------------------------------- CRUD
Q_CREAR_USUARIO = """
CREATE (u:Usuario {id: $id, fecha_registro: date()})
SET u += $props
RETURN u {.*, fecha_registro: toString(u.fecha_registro)} AS usuario
"""

Q_LISTAR_USUARIOS = """
MATCH (u:Usuario)
WHERE $texto = '' OR toLower(u.nombre) CONTAINS toLower($texto)
   OR toLower(coalesce(u.titular, '')) CONTAINS toLower($texto)
   OR toLower(coalesce(u.ciudad, '')) CONTAINS toLower($texto)
OPTIONAL MATCH (u)-[:TRABAJA_EN {actual: true}]->(e:Empresa)
WITH u, collect(e.nombre)[0] AS empresa_actual
RETURN u.id AS id, u.nombre AS nombre, u.titular AS titular, u.ciudad AS ciudad,
       u.email AS email, u.anios_experiencia AS anios_experiencia, empresa_actual,
       coalesce(u.rol, 'profesional') AS rol, coalesce(u.activo, true) AS activo,
       u.password_hash IS NOT NULL AS tiene_password, toString(u.ultimo_acceso) AS ultimo_acceso,
       COUNT { (u)-[:CONECTA_CON]-(:Usuario) } AS conexiones,
       COUNT { (u)-[:TIENE_HABILIDAD]->() } AS habilidades
ORDER BY nombre
"""

Q_OBTENER_USUARIO = """
MATCH (u:Usuario {id: $id})
RETURN u {.*, fecha_registro: toString(u.fecha_registro), actualizado: toString(u.actualizado),
          ultimo_acceso: toString(u.ultimo_acceso), rol: coalesce(u.rol, 'profesional')} AS usuario,
  [(u)-[r:TIENE_HABILIDAD]->(h:Habilidad) | {habilidad: h.nombre, categoria: h.categoria, nivel: r.nivel}] AS habilidades,
  [(u)-[r:TRABAJA_EN]->(e:Empresa) | {empresa_id: e.id, empresa: e.nombre, cargo: r.cargo, desde: r.desde, actual: r.actual}] AS empresas,
  [(u)-[r:PARTICIPA_EN]->(p:Proyecto) | {proyecto_id: p.id, proyecto: p.nombre, rol: r.rol}] AS proyectos,
  [(u)-[:CONECTA_CON]-(c:Usuario) | {id: c.id, nombre: c.nombre, titular: c.titular}] AS conexiones,
  [(u)-[r:POSTULA_A]->(o:Oferta)<-[:PUBLICA]-(e:Empresa) |
     {oferta_id: o.id, oferta: o.titulo, empresa: e.nombre, estado: r.estado, fecha: toString(r.fecha)}] AS postulaciones
"""

Q_ACTUALIZAR_USUARIO = """
MATCH (u:Usuario {id: $id})
SET u += $props, u.actualizado = datetime()
RETURN u {.*, fecha_registro: toString(u.fecha_registro), actualizado: toString(u.actualizado)} AS usuario
"""

Q_ELIMINAR_USUARIO = """
MATCH (u:Usuario {id: $id})
WITH u, COUNT { (u)--() } AS relaciones
DETACH DELETE u
RETURN relaciones
"""

# ---------------------------------------------------------------- Vínculos
Q_ASIGNAR_HABILIDAD = """
MATCH (u:Usuario {id: $usuario_id})
MERGE (h:Habilidad {nombre: $habilidad})
  ON CREATE SET h.categoria = coalesce($categoria, 'General')
MERGE (u)-[r:TIENE_HABILIDAD]->(h)
SET r.nivel = $nivel
RETURN u.nombre AS usuario, h.nombre AS habilidad, r.nivel AS nivel
"""

Q_QUITAR_HABILIDAD = """
MATCH (:Usuario {id: $usuario_id})-[r:TIENE_HABILIDAD]->(:Habilidad {nombre: $habilidad})
DELETE r RETURN count(*) AS eliminadas
"""

Q_VINCULAR_EMPRESA = """
MATCH (u:Usuario {id: $usuario_id}), (e:Empresa {id: $empresa_id})
MERGE (u)-[r:TRABAJA_EN]->(e)
SET r.cargo = $cargo, r.desde = $desde, r.actual = $actual
RETURN u.nombre AS usuario, e.nombre AS empresa, r.cargo AS cargo
"""

Q_DESVINCULAR_EMPRESA = """
MATCH (:Usuario {id: $usuario_id})-[r:TRABAJA_EN]->(:Empresa {id: $empresa_id})
DELETE r RETURN count(*) AS eliminadas
"""

Q_VINCULAR_PROYECTO = """
MATCH (u:Usuario {id: $usuario_id}), (p:Proyecto {id: $proyecto_id})
MERGE (u)-[r:PARTICIPA_EN]->(p)
SET r.rol = $rol
RETURN u.nombre AS usuario, p.nombre AS proyecto, r.rol AS rol
"""

Q_DESVINCULAR_PROYECTO = """
MATCH (:Usuario {id: $usuario_id})-[r:PARTICIPA_EN]->(:Proyecto {id: $proyecto_id})
DELETE r RETURN count(*) AS eliminadas
"""

# CONECTA_CON se almacena con una dirección pero se consulta SIN dirección (relación simétrica).
Q_CONECTAR = """
MATCH (a:Usuario {id: $a}), (b:Usuario {id: $b})
WHERE a <> b AND NOT (a)-[:CONECTA_CON]-(b)
CREATE (a)-[:CONECTA_CON {desde: date()}]->(b)
RETURN a.nombre AS origen, b.nombre AS destino
"""

Q_DESCONECTAR = """
MATCH (:Usuario {id: $a})-[r:CONECTA_CON]-(:Usuario {id: $b})
DELETE r RETURN count(*) AS eliminadas
"""

Q_POSTULAR = """
MATCH (u:Usuario {id: $usuario_id}), (o:Oferta {id: $oferta_id})
WHERE coalesce(o.activa, true)
MERGE (u)-[r:POSTULA_A]->(o)
  ON CREATE SET r.fecha = date(), r.estado = 'Enviada'
RETURN u.nombre AS usuario, o.titulo AS oferta, r.estado AS estado, toString(r.fecha) AS fecha
"""

Q_RETIRAR_POSTULACION = """
MATCH (:Usuario {id: $usuario_id})-[r:POSTULA_A]->(:Oferta {id: $oferta_id})
DELETE r RETURN count(*) AS eliminadas
"""

Q_ESTADO_POSTULACION = """
MATCH (:Usuario {id: $usuario_id})-[r:POSTULA_A]->(:Oferta {id: $oferta_id})
SET r.estado = $estado RETURN r.estado AS estado
"""


# ---------------------------------------------------------------- Invitaciones de conexión
# (:Usuario)-[:SOLICITA_CONEXION {fecha}]->(:Usuario)  — al aceptarse se convierte en CONECTA_CON
Q_INVITACION_INVERSA = "RETURN EXISTS { (:Usuario {id: $b})-[:SOLICITA_CONEXION]->(:Usuario {id: $a}) } AS existe"

Q_ENVIAR_INVITACION = """
MATCH (a:Usuario {id: $a}), (b:Usuario {id: $b})
WHERE a <> b AND NOT (a)-[:CONECTA_CON]-(b)
MERGE (a)-[s:SOLICITA_CONEXION]->(b) ON CREATE SET s.fecha = datetime()
RETURN b.nombre AS destino
"""

Q_ACEPTAR_INVITACION = """
MATCH (emisor:Usuario {id: $emisor})-[s:SOLICITA_CONEXION]->(receptor:Usuario {id: $receptor})
DELETE s
WITH emisor, receptor
WHERE NOT (emisor)-[:CONECTA_CON]-(receptor)
CREATE (emisor)-[:CONECTA_CON {desde: date()}]->(receptor)
RETURN emisor.nombre AS nombre
"""

Q_BORRAR_INVITACION = """
MATCH (:Usuario {id: $emisor})-[s:SOLICITA_CONEXION]->(:Usuario {id: $receptor})
DELETE s RETURN count(*) AS eliminadas
"""

Q_INVITACIONES_RECIBIDAS = """
MATCH (e:Usuario)-[s:SOLICITA_CONEXION]->(:Usuario {id: $id})
RETURN e.id AS id, e.nombre AS nombre, e.titular AS titular, toString(date(s.fecha)) AS fecha,
       COUNT { (e)-[:CONECTA_CON]-(:Usuario)-[:CONECTA_CON]-(:Usuario {id: $id}) } AS en_comun
ORDER BY s.fecha DESC
"""

Q_INVITACIONES_ENVIADAS = """
MATCH (:Usuario {id: $id})-[s:SOLICITA_CONEXION]->(d:Usuario)
RETURN d.id AS id, d.nombre AS nombre, d.titular AS titular, toString(date(s.fecha)) AS fecha
ORDER BY s.fecha DESC
"""

# Perfil de otra persona visto por el usuario actual: qué tienen en común y en qué estado está la relación.
# Los datos de contacto (correo, teléfono) solo se devuelven si ya están conectados.
Q_PERFIL_PUBLICO = """
MATCH (yo:Usuario {id: $yo}), (o:Usuario {id: $otro})
WITH yo, o, EXISTS { (yo)-[:CONECTA_CON]-(o) } AS conectados
OPTIONAL MATCH ruta = shortestPath((yo)-[:CONECTA_CON*..6]-(o))
RETURN o.id AS id, o.nombre AS nombre, o.titular AS titular, o.ciudad AS ciudad, o.resumen AS resumen,
       o.anios_experiencia AS anios_experiencia, o.nivel_educativo AS nivel_educativo, coalesce(o.rol, 'profesional') AS rol,
       CASE WHEN conectados THEN o.email END AS email, CASE WHEN conectados THEN o.telefono END AS telefono,
       conectados,
       EXISTS { (yo)-[:SOLICITA_CONEXION]->(o) } AS invitacion_enviada,
       EXISTS { (o)-[:SOLICITA_CONEXION]->(yo) } AS invitacion_recibida,
       CASE WHEN ruta IS NULL THEN null ELSE length(ruta) END AS grado,
       [(o)-[r:TIENE_HABILIDAD]->(h:Habilidad) |
          {habilidad: h.nombre, nivel: r.nivel, compartida: EXISTS { (yo)-[:TIENE_HABILIDAD]->(h) }}] AS habilidades,
       [(o)-[r:TRABAJA_EN]->(e:Empresa) |
          {empresa: e.nombre, cargo: r.cargo, desde: r.desde, actual: r.actual,
           compartida: EXISTS { (yo)-[:TRABAJA_EN]->(e) }}] AS empresas,
       [(o)-[r:PARTICIPA_EN]->(p:Proyecto) |
          {proyecto: p.nombre, rol: r.rol, compartido: EXISTS { (yo)-[:PARTICIPA_EN]->(p) }}] AS proyectos,
       COLLECT { MATCH (yo)-[:CONECTA_CON]-(c:Usuario)-[:CONECTA_CON]-(o) RETURN DISTINCT c.nombre } AS contactos_en_comun,
       COUNT { (o)-[:CONECTA_CON]-(:Usuario) } AS total_conexiones
"""

Q_EMAIL_DE_OTRO ="RETURN EXISTS { (u:Usuario {email: $email}) WHERE u.id <> $id } AS existe"


def enviar_invitacion(a: str, b: str) -> str:
    """Envía una invitación de a hacia b. Si b ya había invitado a a, se conectan directamente.

    Devuelve 'conectados', 'enviada' o 'ya_conectados'."""
    if a == b:
        raise ValueError("No puede enviarse una invitación a sí mismo.")
    if leer("RETURN EXISTS { (:Usuario {id: $a})-[:CONECTA_CON]-(:Usuario {id: $b}) } AS c", a=a, b=b)[0]["c"]:
        return "ya_conectados"
    if leer(Q_INVITACION_INVERSA, a=a, b=b)[0]["existe"]:
        escribir(Q_ACEPTAR_INVITACION, emisor=b, receptor=a)
        return "conectados"
    escribir(Q_ENVIAR_INVITACION, a=a, b=b)
    return "enviada"


def aceptar_invitacion(receptor: str, emisor: str) -> bool:
    return bool(escribir(Q_ACEPTAR_INVITACION, emisor=emisor, receptor=receptor))


def rechazar_invitacion(receptor: str, emisor: str) -> int:
    return escribir(Q_BORRAR_INVITACION, emisor=emisor, receptor=receptor)[0]["eliminadas"]


def cancelar_invitacion(emisor: str, receptor: str) -> int:
    return escribir(Q_BORRAR_INVITACION, emisor=emisor, receptor=receptor)[0]["eliminadas"]


def invitaciones_recibidas(id: str) -> list[dict]:
    return leer(Q_INVITACIONES_RECIBIDAS, id=id)


def invitaciones_enviadas(id: str) -> list[dict]:
    return leer(Q_INVITACIONES_ENVIADAS, id=id)


def perfil_publico(yo: str, otro: str) -> dict | None:
    """Perfil de `otro` tal como lo ve `yo`, con lo que tienen en común."""
    r = leer(Q_PERFIL_PUBLICO, yo=yo, otro=otro)
    return r[0] if r else None


def email_en_uso_por_otro(email: str, id: str) -> bool:
    return leer(Q_EMAIL_DE_OTRO, email=(email or "").strip().lower(), id=id)[0]["existe"]


def _sin_sensibles(d: dict | None) -> dict | None:
    from .seguridad import publico
    return publico(d)


def nuevo_id(prefijo: str) -> str:
    return f"{prefijo}-{uuid.uuid4().hex[:8].upper()}"


def _limpiar(props: dict) -> dict:
    out = {k: v for k, v in props.items() if k in CAMPOS_USUARIO and v not in (None, "")}
    if "anios_experiencia" in out:
        out["anios_experiencia"] = int(out["anios_experiencia"])
    if "email" in out:
        out["email"] = str(out["email"]).strip().lower()
    return out


def crear_usuario(props: dict, id: str | None = None) -> dict:
    datos = _limpiar(props)
    if not datos.get("nombre") or not datos.get("email"):
        raise ValueError("El nombre y el correo electrónico son obligatorios.")
    return _sin_sensibles(escribir(Q_CREAR_USUARIO, id=id or nuevo_id("U"), props=datos)[0]["usuario"])


def listar_usuarios(texto: str = "") -> list[dict]:
    return leer(Q_LISTAR_USUARIOS, texto=(texto or "").strip())


def obtener_usuario(id: str) -> dict | None:
    r = leer(Q_OBTENER_USUARIO, id=id)
    if not r:
        return None
    r[0]["usuario"] = _sin_sensibles(r[0]["usuario"])
    return r[0]


def actualizar_usuario(id: str, props: dict) -> dict | None:
    datos = _limpiar(props)
    if "email" in datos and email_en_uso_por_otro(datos["email"], id):
        raise ValueError("Ese correo ya está registrado por otra cuenta.")
    r = escribir(Q_ACTUALIZAR_USUARIO, id=id, props=datos)
    return _sin_sensibles(r[0]["usuario"]) if r else None


def eliminar_usuario(id: str) -> int | None:
    """Elimina el usuario y todas sus relaciones. Devuelve cuántas relaciones tenía (None si no existía)."""
    r = escribir(Q_ELIMINAR_USUARIO, id=id)
    return r[0]["relaciones"] if r else None


def asignar_habilidad(usuario_id: str, habilidad: str, nivel: int = 3, categoria: str | None = None) -> dict:
    return escribir(Q_ASIGNAR_HABILIDAD, usuario_id=usuario_id, habilidad=habilidad.strip(),
                    nivel=int(nivel), categoria=categoria)[0]


def quitar_habilidad(usuario_id: str, habilidad: str) -> int:
    return escribir(Q_QUITAR_HABILIDAD, usuario_id=usuario_id, habilidad=habilidad)[0]["eliminadas"]


def vincular_empresa(usuario_id: str, empresa_id: str, cargo: str, desde: int | None = None, actual: bool = True) -> dict:
    return escribir(Q_VINCULAR_EMPRESA, usuario_id=usuario_id, empresa_id=empresa_id, cargo=cargo,
                    desde=int(desde) if desde else date.today().year, actual=bool(actual))[0]


def desvincular_empresa(usuario_id: str, empresa_id: str) -> int:
    return escribir(Q_DESVINCULAR_EMPRESA, usuario_id=usuario_id, empresa_id=empresa_id)[0]["eliminadas"]


def vincular_proyecto(usuario_id: str, proyecto_id: str, rol: str = "Colaborador") -> dict:
    return escribir(Q_VINCULAR_PROYECTO, usuario_id=usuario_id, proyecto_id=proyecto_id, rol=rol)[0]


def desvincular_proyecto(usuario_id: str, proyecto_id: str) -> int:
    return escribir(Q_DESVINCULAR_PROYECTO, usuario_id=usuario_id, proyecto_id=proyecto_id)[0]["eliminadas"]


def conectar(a: str, b: str) -> dict | None:
    """Crea la conexión profesional. Devuelve None si ya estaban conectados."""
    if a == b:
        raise ValueError("Un usuario no puede conectarse consigo mismo.")
    r = escribir(Q_CONECTAR, a=a, b=b)
    return r[0] if r else None


def desconectar(a: str, b: str) -> int:
    return escribir(Q_DESCONECTAR, a=a, b=b)[0]["eliminadas"]


def postular(usuario_id: str, oferta_id: str) -> dict | None:
    """Crea la postulación (idempotente). None si la oferta no existe o está cerrada."""
    r = escribir(Q_POSTULAR, usuario_id=usuario_id, oferta_id=oferta_id)
    return r[0] if r else None


def retirar_postulacion(usuario_id: str, oferta_id: str) -> int:
    return escribir(Q_RETIRAR_POSTULACION, usuario_id=usuario_id, oferta_id=oferta_id)[0]["eliminadas"]


def cambiar_estado_postulacion(usuario_id: str, oferta_id: str, estado: str) -> None:
    escribir(Q_ESTADO_POSTULACION, usuario_id=usuario_id, oferta_id=oferta_id, estado=estado)
