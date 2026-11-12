"""Restricciones de unicidad, índices y utilidades de administración."""
from __future__ import annotations

from .db import leer, escribir, get_driver, database

RESTRICCIONES = [
    "CREATE CONSTRAINT usuario_id IF NOT EXISTS FOR (u:Usuario) REQUIRE u.id IS UNIQUE",
    "CREATE CONSTRAINT usuario_email IF NOT EXISTS FOR (u:Usuario) REQUIRE u.email IS UNIQUE",
    "CREATE CONSTRAINT empresa_id IF NOT EXISTS FOR (e:Empresa) REQUIRE e.id IS UNIQUE",
    "CREATE CONSTRAINT empresa_nombre IF NOT EXISTS FOR (e:Empresa) REQUIRE e.nombre IS UNIQUE",
    "CREATE CONSTRAINT habilidad_nombre IF NOT EXISTS FOR (h:Habilidad) REQUIRE h.nombre IS UNIQUE",
    "CREATE CONSTRAINT proyecto_id IF NOT EXISTS FOR (p:Proyecto) REQUIRE p.id IS UNIQUE",
    "CREATE CONSTRAINT oferta_id IF NOT EXISTS FOR (o:Oferta) REQUIRE o.id IS UNIQUE",
]

INDICES = [
    "CREATE INDEX usuario_nombre IF NOT EXISTS FOR (u:Usuario) ON (u.nombre)",
    "CREATE INDEX usuario_ciudad IF NOT EXISTS FOR (u:Usuario) ON (u.ciudad)",
    "CREATE INDEX habilidad_categoria IF NOT EXISTS FOR (h:Habilidad) ON (h.categoria)",
    "CREATE INDEX oferta_activa IF NOT EXISTS FOR (o:Oferta) ON (o.activa)",
    "CREATE INDEX usuario_sesion IF NOT EXISTS FOR (u:Usuario) ON (u.sesion_hash)",
]

# Distingue datos de demostración (propiedad demo) de los creados por usuarios reales
Q_ORIGEN_DATOS = """
UNWIND ['Usuario','Empresa','Habilidad','Proyecto','Oferta'] AS etiqueta
CALL (etiqueta) {
  MATCH (n) WHERE etiqueta IN labels(n)
  RETURN sum(CASE WHEN n.demo IS NOT NULL THEN 1 ELSE 0 END) AS demo,
         sum(CASE WHEN n.demo IS NULL THEN 1 ELSE 0 END) AS reales
}
RETURN etiqueta, demo, reales
"""

# Borra SOLO los nodos de demostración del lote indicado. Conserva habilidades y empresas de
# demostración que ya estén vinculadas a datos reales (para no romper perfiles de usuarios reales)
# y les quita la marca demo, convirtiéndolas en datos permanentes.
Q_BORRAR_DEMO = """
MATCH (n {demo: $lote})
WHERE NOT ((n:Habilidad OR n:Empresa) AND EXISTS { (n)--(m) WHERE m.demo IS NULL OR m.demo <> $lote })
WITH collect(n) AS nodos
FOREACH (n IN nodos | DETACH DELETE n)
RETURN size(nodos) AS eliminados
"""

Q_CONSERVAR_RESTANTES = "MATCH (n {demo: $lote}) REMOVE n.demo RETURN count(n) AS conservados"

Q_CONTEO_NODOS = """
UNWIND ['Usuario','Empresa','Habilidad','Proyecto','Oferta'] AS etiqueta
CALL (etiqueta) {
  MATCH (n) WHERE etiqueta IN labels(n) RETURN count(n) AS total
}
RETURN etiqueta, total
"""

Q_CONTEO_RELACIONES = """
MATCH ()-[r]->() RETURN type(r) AS tipo, count(r) AS total ORDER BY total DESC
"""

Q_TOTAL = "MATCH (n) RETURN count(n) AS nodos"

Q_BORRAR_TODO = "MATCH (n) CALL (n) { DETACH DELETE n } IN TRANSACTIONS OF 1000 ROWS"


def crear_esquema() -> list[str]:
    for q in RESTRICCIONES + INDICES:
        escribir(q)
    return [r["name"] for r in leer("SHOW CONSTRAINTS YIELD name RETURN name ORDER BY name")]


def listar_restricciones() -> list[dict]:
    return leer(
        "SHOW CONSTRAINTS YIELD name, labelsOrTypes, properties, type "
        "RETURN name, labelsOrTypes, properties, type ORDER BY name"
    )


def conteo_nodos() -> dict[str, int]:
    return {r["etiqueta"]: r["total"] for r in leer(Q_CONTEO_NODOS)}


def conteo_relaciones() -> dict[str, int]:
    return {r["tipo"]: r["total"] for r in leer(Q_CONTEO_RELACIONES)}


def total_nodos() -> int:
    return leer(Q_TOTAL)[0]["nodos"]


def origen_datos() -> list[dict]:
    return leer(Q_ORIGEN_DATOS)


def borrar_datos_demo(confirmacion: str, lote: str = "orbita-demo") -> dict:
    """Elimina solo los datos de demostración. Exige escribir 'BORRAR DEMO'."""
    if confirmacion != "BORRAR DEMO":
        raise PermissionError("Confirmación incorrecta: no se eliminó nada.")
    eliminados = escribir(Q_BORRAR_DEMO, lote=lote)[0]["eliminados"]
    conservados = escribir(Q_CONSERVAR_RESTANTES, lote=lote)[0]["conservados"]
    return {"eliminados": eliminados, "conservados": conservados}


def borrar_todo(confirmacion: str) -> bool:
    """Elimina TODO el grafo. Exige la palabra exacta 'BORRAR' como salvaguarda.

    Nunca se invoca automáticamente: solo desde la página de Administración o el
    script de inicialización, tras mostrar el contenido actual y pedir confirmación.
    """
    if confirmacion != "BORRAR":
        raise PermissionError("Confirmación incorrecta: no se eliminó nada.")
    # CALL ... IN TRANSACTIONS requiere una transacción implícita (session.run)
    with get_driver().session(database=database()) as s:
        s.run(Q_BORRAR_TODO).consume()
    return True
