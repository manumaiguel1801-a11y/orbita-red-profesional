"""CRUD de Empresa, Habilidad, Proyecto y Oferta, y sus relaciones PUBLICA, REQUIERE y USA_TECNOLOGIA."""
from __future__ import annotations

from datetime import date

from .db import leer, escribir
from .usuarios import nuevo_id

# ================================================================ EMPRESAS
Q_CREAR_EMPRESA = """
CREATE (e:Empresa {id: $id}) SET e += $props
RETURN e {.*} AS empresa
"""

Q_LISTAR_EMPRESAS = """
MATCH (e:Empresa)
RETURN e.id AS id, e.nombre AS nombre, e.sector AS sector, e.ciudad AS ciudad, e.tamano AS tamano,
       e.sitio_web AS sitio_web, e.descripcion AS descripcion,
       COUNT { (e)<-[:TRABAJA_EN {actual: true}]-(:Usuario) } AS empleados,
       COUNT { (e)-[:PUBLICA]->(:Oferta) } AS ofertas
ORDER BY nombre
"""

Q_ACTUALIZAR_EMPRESA = "MATCH (e:Empresa {id: $id}) SET e += $props RETURN e {.*} AS empresa"

Q_ELIMINAR_EMPRESA = """
MATCH (e:Empresa {id: $id})
OPTIONAL MATCH (e)-[:PUBLICA]->(o:Oferta)
WITH e, collect(o) AS ofertas
FOREACH (o IN ofertas | DETACH DELETE o)
DETACH DELETE e
RETURN size(ofertas) AS ofertas_eliminadas
"""

# ================================================================ HABILIDADES
Q_CREAR_HABILIDAD = """
MERGE (h:Habilidad {nombre: $nombre})
SET h.categoria = $categoria
RETURN h {.*} AS habilidad
"""

Q_LISTAR_HABILIDADES = """
MATCH (h:Habilidad)
RETURN h.nombre AS nombre, h.categoria AS categoria,
       COUNT { (h)<-[:TIENE_HABILIDAD]-(:Usuario) } AS usuarios,
       COUNT { (h)<-[:REQUIERE]-(:Oferta) } AS ofertas,
       COUNT { (h)<-[:USA_TECNOLOGIA]-(:Proyecto) } AS proyectos
ORDER BY categoria, nombre
"""

Q_ACTUALIZAR_HABILIDAD = """
MATCH (h:Habilidad {nombre: $nombre})
SET h.nombre = $nuevo_nombre, h.categoria = $categoria
RETURN h {.*} AS habilidad
"""

Q_ELIMINAR_HABILIDAD = """
MATCH (h:Habilidad {nombre: $nombre})
WITH h, COUNT { (h)--() } AS relaciones
DETACH DELETE h RETURN relaciones
"""

# ================================================================ PROYECTOS
Q_CREAR_PROYECTO = """
CREATE (p:Proyecto {id: $id}) SET p += $props
RETURN p {.*} AS proyecto
"""

Q_LISTAR_PROYECTOS = """
MATCH (p:Proyecto)
RETURN p.id AS id, p.nombre AS nombre, p.descripcion AS descripcion, p.estado AS estado, p.anio AS anio,
       [(p)-[:USA_TECNOLOGIA]->(h:Habilidad) | h.nombre] AS tecnologias,
       [(u:Usuario)-[:PARTICIPA_EN]->(p) | u.nombre] AS miembros
ORDER BY nombre
"""

Q_ACTUALIZAR_PROYECTO = "MATCH (p:Proyecto {id: $id}) SET p += $props RETURN p {.*} AS proyecto"

Q_ELIMINAR_PROYECTO = "MATCH (p:Proyecto {id: $id}) DETACH DELETE p RETURN count(*) AS eliminados"

Q_AGREGAR_TECNOLOGIA = """
MATCH (p:Proyecto {id: $proyecto_id})
MERGE (h:Habilidad {nombre: $habilidad})
  ON CREATE SET h.categoria = 'General'
MERGE (p)-[:USA_TECNOLOGIA]->(h)
RETURN p.nombre AS proyecto, h.nombre AS tecnologia
"""

Q_QUITAR_TECNOLOGIA = """
MATCH (:Proyecto {id: $proyecto_id})-[r:USA_TECNOLOGIA]->(:Habilidad {nombre: $habilidad})
DELETE r RETURN count(*) AS eliminadas
"""

# ================================================================ OFERTAS
# PUBLICA se crea en la misma transacción: una oferta siempre pertenece a una empresa.
Q_CREAR_OFERTA = """
MATCH (e:Empresa {id: $empresa_id})
CREATE (e)-[:PUBLICA {fecha: date()}]->(o:Oferta {id: $id, fecha_publicacion: date(), activa: true})
SET o += $props
WITH e, o
UNWIND $requisitos AS req
MERGE (h:Habilidad {nombre: req.habilidad})
  ON CREATE SET h.categoria = 'General'
MERGE (o)-[r:REQUIERE]->(h)
SET r.nivel_minimo = req.nivel_minimo, r.obligatoria = req.obligatoria
RETURN o.id AS id, e.nombre AS empresa, count(h) AS habilidades
"""

Q_CREAR_OFERTA_SIN_REQ = """
MATCH (e:Empresa {id: $empresa_id})
CREATE (e)-[:PUBLICA {fecha: date()}]->(o:Oferta {id: $id, fecha_publicacion: date(), activa: true})
SET o += $props
RETURN o.id AS id, e.nombre AS empresa, 0 AS habilidades
"""

Q_LISTAR_OFERTAS = """
MATCH (e:Empresa)-[:PUBLICA]->(o:Oferta)
WHERE ($solo_activas = false OR o.activa) AND ($empresa_id = '' OR e.id = $empresa_id)
RETURN o.id AS id, o.titulo AS titulo, e.nombre AS empresa, e.id AS empresa_id, o.ciudad AS ciudad,
       o.modalidad AS modalidad, o.nivel AS nivel, o.salario AS salario, o.activa AS activa,
       toString(o.fecha_publicacion) AS fecha_publicacion, o.descripcion AS descripcion,
       [(o)-[r:REQUIERE]->(h:Habilidad) | {habilidad: h.nombre, nivel_minimo: r.nivel_minimo, obligatoria: r.obligatoria}] AS requisitos,
       COUNT { (o)<-[:POSTULA_A]-(:Usuario) } AS postulantes
ORDER BY fecha_publicacion DESC, titulo
"""

Q_ACTUALIZAR_OFERTA = "MATCH (o:Oferta {id: $id}) SET o += $props RETURN o {.*, fecha_publicacion: toString(o.fecha_publicacion)} AS oferta"

Q_ELIMINAR_OFERTA = "MATCH (o:Oferta {id: $id}) DETACH DELETE o RETURN count(*) AS eliminadas"

Q_AGREGAR_REQUISITO = """
MATCH (o:Oferta {id: $oferta_id})
MERGE (h:Habilidad {nombre: $habilidad})
  ON CREATE SET h.categoria = 'General'
MERGE (o)-[r:REQUIERE]->(h)
SET r.nivel_minimo = $nivel_minimo, r.obligatoria = $obligatoria
RETURN o.titulo AS oferta, h.nombre AS habilidad
"""

Q_QUITAR_REQUISITO = """
MATCH (:Oferta {id: $oferta_id})-[r:REQUIERE]->(:Habilidad {nombre: $habilidad})
DELETE r RETURN count(*) AS eliminadas
"""

Q_POSTULANTES = """
MATCH (u:Usuario)-[r:POSTULA_A]->(o:Oferta {id: $oferta_id})
RETURN u.id AS id, u.nombre AS nombre, u.titular AS titular, r.estado AS estado, toString(r.fecha) AS fecha,
       size([(o)-[:REQUIERE]->(h)<-[:TIENE_HABILIDAD]-(u) | h]) AS habilidades_cumplidas,
       COUNT { (o)-[:REQUIERE]->() } AS habilidades_requeridas
ORDER BY habilidades_cumplidas DESC, nombre
"""


def _sin_vacios(d: dict) -> dict:
    return {k: v for k, v in d.items() if v not in (None, "")}


# ---- Empresas
def crear_empresa(props: dict, id: str | None = None) -> dict:
    if not props.get("nombre"):
        raise ValueError("El nombre de la empresa es obligatorio.")
    return escribir(Q_CREAR_EMPRESA, id=id or nuevo_id("E"), props=_sin_vacios(props))[0]["empresa"]


def listar_empresas() -> list[dict]:
    return leer(Q_LISTAR_EMPRESAS)


def actualizar_empresa(id: str, props: dict) -> dict | None:
    r = escribir(Q_ACTUALIZAR_EMPRESA, id=id, props=_sin_vacios(props))
    return r[0]["empresa"] if r else None


def eliminar_empresa(id: str) -> int | None:
    """Elimina la empresa y en cascada sus ofertas (una oferta no existe sin su empresa)."""
    r = escribir(Q_ELIMINAR_EMPRESA, id=id)
    return r[0]["ofertas_eliminadas"] if r else None


# ---- Habilidades
def crear_habilidad(nombre: str, categoria: str = "General") -> dict:
    if not nombre.strip():
        raise ValueError("El nombre de la habilidad es obligatorio.")
    return escribir(Q_CREAR_HABILIDAD, nombre=nombre.strip(), categoria=categoria)[0]["habilidad"]


def listar_habilidades() -> list[dict]:
    return leer(Q_LISTAR_HABILIDADES)


def actualizar_habilidad(nombre: str, nuevo_nombre: str, categoria: str) -> dict | None:
    r = escribir(Q_ACTUALIZAR_HABILIDAD, nombre=nombre, nuevo_nombre=nuevo_nombre.strip(), categoria=categoria)
    return r[0]["habilidad"] if r else None


def eliminar_habilidad(nombre: str) -> int | None:
    r = escribir(Q_ELIMINAR_HABILIDAD, nombre=nombre)
    return r[0]["relaciones"] if r else None


# ---- Proyectos
def crear_proyecto(props: dict, tecnologias: list[str] | None = None, id: str | None = None) -> dict:
    if not props.get("nombre"):
        raise ValueError("El nombre del proyecto es obligatorio.")
    p = escribir(Q_CREAR_PROYECTO, id=id or nuevo_id("P"), props=_sin_vacios(props))[0]["proyecto"]
    for t in tecnologias or []:
        agregar_tecnologia(p["id"], t)
    return p


def listar_proyectos() -> list[dict]:
    return leer(Q_LISTAR_PROYECTOS)


def actualizar_proyecto(id: str, props: dict) -> dict | None:
    r = escribir(Q_ACTUALIZAR_PROYECTO, id=id, props=_sin_vacios(props))
    return r[0]["proyecto"] if r else None


def eliminar_proyecto(id: str) -> int:
    return escribir(Q_ELIMINAR_PROYECTO, id=id)[0]["eliminados"]


def agregar_tecnologia(proyecto_id: str, habilidad: str) -> dict:
    return escribir(Q_AGREGAR_TECNOLOGIA, proyecto_id=proyecto_id, habilidad=habilidad.strip())[0]


def quitar_tecnologia(proyecto_id: str, habilidad: str) -> int:
    return escribir(Q_QUITAR_TECNOLOGIA, proyecto_id=proyecto_id, habilidad=habilidad)[0]["eliminadas"]


# ---- Ofertas
def crear_oferta(empresa_id: str, props: dict, requisitos: list[dict] | None = None, id: str | None = None) -> dict:
    """requisitos: [{'habilidad': str, 'nivel_minimo': int, 'obligatoria': bool}]"""
    if not props.get("titulo"):
        raise ValueError("El título de la oferta es obligatorio.")
    reqs = [
        {"habilidad": r["habilidad"].strip(), "nivel_minimo": int(r.get("nivel_minimo", 3)),
         "obligatoria": bool(r.get("obligatoria", True))}
        for r in (requisitos or []) if r.get("habilidad")
    ]
    q = Q_CREAR_OFERTA if reqs else Q_CREAR_OFERTA_SIN_REQ
    r = escribir(q, empresa_id=empresa_id, id=id or nuevo_id("O"), props=_sin_vacios(props), requisitos=reqs)
    if not r:
        raise ValueError("La empresa indicada no existe.")
    return r[0]


def listar_ofertas(solo_activas: bool = False, empresa_id: str = "") -> list[dict]:
    return leer(Q_LISTAR_OFERTAS, solo_activas=solo_activas, empresa_id=empresa_id or "")


def actualizar_oferta(id: str, props: dict) -> dict | None:
    limpio = {k: v for k, v in props.items() if v is not None and v != ""}
    r = escribir(Q_ACTUALIZAR_OFERTA, id=id, props=limpio)
    return r[0]["oferta"] if r else None


def eliminar_oferta(id: str) -> int:
    return escribir(Q_ELIMINAR_OFERTA, id=id)[0]["eliminadas"]


def agregar_requisito(oferta_id: str, habilidad: str, nivel_minimo: int = 3, obligatoria: bool = True) -> dict:
    return escribir(Q_AGREGAR_REQUISITO, oferta_id=oferta_id, habilidad=habilidad.strip(),
                    nivel_minimo=int(nivel_minimo), obligatoria=bool(obligatoria))[0]


def quitar_requisito(oferta_id: str, habilidad: str) -> int:
    return escribir(Q_QUITAR_REQUISITO, oferta_id=oferta_id, habilidad=habilidad)[0]["eliminadas"]


def postulantes(oferta_id: str) -> list[dict]:
    return leer(Q_POSTULANTES, oferta_id=oferta_id)


def hoy() -> str:
    return date.today().isoformat()


# ================================================================ Permisos (reclutador / admin)
Q_EMPRESAS_ACTUALES = """
MATCH (:Usuario {id: $id})-[:TRABAJA_EN {actual: true}]->(e:Empresa)
RETURN e.id AS id, e.nombre AS nombre ORDER BY nombre
"""

Q_PUEDE_PUBLICAR = """
MATCH (u:Usuario {id: $actor})
RETURN coalesce(u.activo, true) AND (u.rol = 'admin' OR (u.rol = 'reclutador'
       AND EXISTS { (u)-[:TRABAJA_EN {actual: true}]->(:Empresa {id: $empresa_id}) })) AS puede
"""

Q_PUEDE_GESTIONAR_OFERTA = """
MATCH (u:Usuario {id: $actor})
RETURN coalesce(u.activo, true) AND (u.rol = 'admin' OR (u.rol = 'reclutador'
       AND EXISTS { (u)-[:TRABAJA_EN {actual: true}]->(:Empresa)-[:PUBLICA]->(:Oferta {id: $oferta_id}) })) AS puede
"""


def empresas_actuales(usuario_id: str) -> list[dict]:
    return leer(Q_EMPRESAS_ACTUALES, id=usuario_id)


def puede_publicar(actor: str, empresa_id: str) -> bool:
    r = leer(Q_PUEDE_PUBLICAR, actor=actor, empresa_id=empresa_id)
    return bool(r) and bool(r[0]["puede"])


def puede_gestionar_oferta(actor: str, oferta_id: str) -> bool:
    r = leer(Q_PUEDE_GESTIONAR_OFERTA, actor=actor, oferta_id=oferta_id)
    return bool(r) and bool(r[0]["puede"])


def _exigir_oferta(actor: str, oferta_id: str) -> None:
    if not puede_gestionar_oferta(actor, oferta_id):
        raise PermissionError("Solo los reclutadores de la empresa que publicó la oferta (o un administrador) pueden gestionarla.")


def validar_oferta(props: dict, requisitos: list[dict] | None = None, exigir_requisitos: bool = True) -> dict[str, str]:
    e = {}
    titulo = (props.get("titulo") or "").strip()
    if not 3 <= len(titulo) <= 120:
        e["titulo"] = "El título debe tener entre 3 y 120 caracteres."
    sal = props.get("salario")
    if sal not in (None, "") and not (0 <= int(sal) <= 200_000_000):
        e["salario"] = "El salario debe estar entre 0 y 200.000.000."
    if len(props.get("descripcion") or "") > 2000:
        e["descripcion"] = "La descripción admite máximo 2000 caracteres."
    if requisitos is not None:
        habs = [r.get("habilidad") for r in requisitos if r.get("habilidad")]
        if exigir_requisitos and not habs:
            e["requisitos"] = "Agregue al menos una habilidad requerida."
        elif len(habs) != len(set(habs)):
            e["requisitos"] = "Hay habilidades repetidas en los requisitos."
        elif any(not 1 <= int(r.get("nivel_minimo") or 0) <= 5 for r in requisitos if r.get("habilidad")):
            e["requisitos"] = "El nivel mínimo debe estar entre 1 y 5."
    return e


def publicar_oferta_como(actor: str, empresa_id: str, props: dict, requisitos: list[dict]) -> dict:
    if not puede_publicar(actor, empresa_id):
        raise PermissionError("Solo puede publicar ofertas para la empresa en la que trabaja actualmente como reclutador.")
    errores = validar_oferta(props, requisitos)
    if errores:
        raise ValueError(" ".join(errores.values()))
    return crear_oferta(empresa_id, props, requisitos)


def actualizar_oferta_como(actor: str, oferta_id: str, props: dict) -> dict | None:
    _exigir_oferta(actor, oferta_id)
    errores = validar_oferta(props)
    if errores:
        raise ValueError(" ".join(errores.values()))
    return actualizar_oferta(oferta_id, props)


def eliminar_oferta_como(actor: str, oferta_id: str) -> int:
    _exigir_oferta(actor, oferta_id)
    return eliminar_oferta(oferta_id)


def agregar_requisito_como(actor: str, oferta_id: str, habilidad: str, nivel_minimo: int, obligatoria: bool) -> dict:
    _exigir_oferta(actor, oferta_id)
    return agregar_requisito(oferta_id, habilidad, nivel_minimo, obligatoria)


def quitar_requisito_como(actor: str, oferta_id: str, habilidad: str) -> int:
    _exigir_oferta(actor, oferta_id)
    return quitar_requisito(oferta_id, habilidad)


def estado_postulacion_como(actor: str, oferta_id: str, usuario_id: str, estado: str) -> None:
    _exigir_oferta(actor, oferta_id)
    from .usuarios import cambiar_estado_postulacion
    cambiar_estado_postulacion(usuario_id, oferta_id, estado)


# ================================================================ Empresas registradas por usuarios
Q_EMPRESA_POR_NOMBRE = """
MATCH (e:Empresa) WHERE toLower(trim(e.nombre)) = toLower(trim($nombre))
RETURN e.id AS id, e.nombre AS nombre LIMIT 1
"""


def buscar_empresa_por_nombre(nombre: str) -> dict | None:
    r = leer(Q_EMPRESA_POR_NOMBRE, nombre=nombre or "")
    return r[0] if r else None


def registrar_empresa(props: dict) -> dict:
    """Registro de empresa desde el perfil de un usuario.

    Valida el nombre (2-80 caracteres) y evita duplicados sin distinguir mayúsculas ni espacios:
    si ya existe una empresa con ese nombre, se devuelve la existente en lugar de crear otra.
    """
    nombre = " ".join((props.get("nombre") or "").split())
    if not 2 <= len(nombre) <= 80:
        raise ValueError("El nombre de la empresa debe tener entre 2 y 80 caracteres.")
    existente = buscar_empresa_por_nombre(nombre)
    if existente:
        return {**existente, "ya_existia": True}
    datos = {k: (v.strip() if isinstance(v, str) else v) for k, v in props.items() if v not in (None, "")}
    datos["nombre"] = nombre
    e = crear_empresa(datos)
    return {"id": e["id"], "nombre": e["nombre"], "ya_existia": False}


# ================================================================ Proyectos creados por usuarios
Q_ES_MIEMBRO = "RETURN EXISTS { (:Usuario {id: $u})-[:PARTICIPA_EN]->(:Proyecto {id: $p}) } AS miembro"


def crear_proyecto_como(actor: str, props: dict, tecnologias: list[str]) -> dict:
    nombre = (props.get("nombre") or "").strip()
    if not 3 <= len(nombre) <= 120:
        raise ValueError("El nombre del proyecto debe tener entre 3 y 120 caracteres.")
    if not tecnologias:
        raise ValueError("Seleccione al menos una tecnología.")
    p = crear_proyecto(props, tecnologias)
    from .usuarios import vincular_proyecto
    vincular_proyecto(actor, p["id"], "Líder")
    return p


def es_miembro(usuario_id: str, proyecto_id: str) -> bool:
    return leer(Q_ES_MIEMBRO, u=usuario_id, p=proyecto_id)[0]["miembro"]


# ================================================================ Búsqueda de ofertas
Q_BUSCAR_OFERTAS = """
MATCH (e:Empresa)-[:PUBLICA]->(o:Oferta)
WHERE coalesce(o.activa, true)
  AND ($texto = '' OR toLower(o.titulo) CONTAINS toLower($texto) OR toLower(e.nombre) CONTAINS toLower($texto))
  AND ($modalidad = '' OR o.modalidad = $modalidad)
  AND ($ciudad = '' OR o.ciudad = $ciudad)
  AND (size($habilidades) = 0 OR ALL(h IN $habilidades WHERE EXISTS { (o)-[:REQUIERE]->(:Habilidad {nombre: h}) }))
OPTIONAL MATCH (o)-[r:REQUIERE]->(h:Habilidad)
OPTIONAL MATCH (:Usuario {id: $usuario_id})-[t:TIENE_HABILIDAD]->(h)
WITH e, o, collect({habilidad: h.nombre, obligatoria: r.obligatoria, nivel_minimo: r.nivel_minimo, tengo: t IS NOT NULL}) AS requisitos
RETURN o.id AS id, o.titulo AS titulo, e.nombre AS empresa, o.ciudad AS ciudad, o.modalidad AS modalidad, o.nivel AS nivel,
       o.salario AS salario, toString(o.fecha_publicacion) AS fecha_publicacion, o.descripcion AS descripcion,
       [x IN requisitos WHERE x.habilidad IS NOT NULL] AS requisitos,
       EXISTS { (:Usuario {id: $usuario_id})-[:POSTULA_A]->(o) } AS postulado,
       COUNT { (o)<-[:POSTULA_A]-() } AS postulantes
ORDER BY o.fecha_publicacion DESC
"""


def buscar_ofertas(usuario_id: str, texto: str = "", modalidad: str = "", ciudad: str = "", habilidades: list[str] | None = None) -> list[dict]:
    return leer(Q_BUSCAR_OFERTAS, usuario_id=usuario_id, texto=(texto or "").strip(), modalidad=modalidad or "",
                ciudad=ciudad or "", habilidades=list(habilidades or []))
