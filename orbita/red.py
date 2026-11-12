"""Consultas de red: contactos en común, usuarios con habilidades similares y rutas más cortas."""
from __future__ import annotations

from .db import leer

# ---------------------------------------------------------------- Contactos en común (B2)
Q_CONTACTOS_EN_COMUN = """
MATCH (a:Usuario {id: $a})-[:CONECTA_CON]-(c:Usuario)-[:CONECTA_CON]-(b:Usuario {id: $b})
WHERE a <> b
RETURN DISTINCT c.id AS id, c.nombre AS nombre, c.titular AS titular, c.ciudad AS ciudad,
       COUNT { (c)-[:CONECTA_CON]-(:Usuario) } AS conexiones
ORDER BY conexiones DESC, nombre
"""

Q_ESTAN_CONECTADOS = """
RETURN EXISTS { (:Usuario {id: $a})-[:CONECTA_CON]-(:Usuario {id: $b}) } AS conectados
"""

# ---------------------------------------------------------------- Habilidades similares (B1)
# Similitud de Jaccard: |H(u) ∩ H(o)| / |H(u) ∪ H(o)|
Q_USUARIOS_SIMILARES = """
MATCH (u:Usuario {id: $id})-[:TIENE_HABILIDAD]->(h:Habilidad)<-[:TIENE_HABILIDAD]-(o:Usuario)
WITH u, o, collect(h.nombre) AS compartidas
WITH u, o, compartidas,
     COUNT { (u)-[:TIENE_HABILIDAD]->() } AS nu,
     COUNT { (o)-[:TIENE_HABILIDAD]->() } AS no
RETURN o.id AS id, o.nombre AS nombre, o.titular AS titular, compartidas,
       size(compartidas) AS en_comun,
       round(toFloat(size(compartidas)) / (nu + no - size(compartidas)), 3) AS jaccard,
       EXISTS { (u)-[:CONECTA_CON]-(o) } AS ya_conectados
ORDER BY jaccard DESC, en_comun DESC, nombre
LIMIT $limite
"""

Q_PARES_SIMILARES = """
MATCH (a:Usuario)-[:TIENE_HABILIDAD]->(h:Habilidad)<-[:TIENE_HABILIDAD]-(b:Usuario)
WHERE a.id < b.id
WITH a, b, collect(h.nombre) AS compartidas
WITH a, b, compartidas,
     COUNT { (a)-[:TIENE_HABILIDAD]->() } AS na,
     COUNT { (b)-[:TIENE_HABILIDAD]->() } AS nb
WHERE size(compartidas) >= $minimo
RETURN a.nombre AS usuario_a, b.nombre AS usuario_b, compartidas, size(compartidas) AS en_comun,
       round(toFloat(size(compartidas)) / (na + nb - size(compartidas)), 3) AS jaccard
ORDER BY jaccard DESC, en_comun DESC
LIMIT $limite
"""

Q_USUARIOS_CON_HABILIDAD = """
MATCH (u:Usuario)-[r:TIENE_HABILIDAD]->(h:Habilidad)
WHERE h.nombre IN $habilidades
WITH u, collect(h.nombre) AS tiene, avg(r.nivel) AS nivel_promedio
RETURN u.id AS id, u.nombre AS nombre, u.titular AS titular, tiene, size(tiene) AS coincidencias,
       round(nivel_promedio, 2) AS nivel_promedio
ORDER BY coincidencias DESC, nivel_promedio DESC
"""

# ---------------------------------------------------------------- Rutas más cortas (B3, A13)
ETIQUETAS = {"Usuario": "id", "Empresa": "id", "Proyecto": "id", "Oferta": "id", "Habilidad": "nombre"}
TIPOS_RELACION = ["CONECTA_CON", "TRABAJA_EN", "TIENE_HABILIDAD", "PARTICIPA_EN", "PUBLICA",
                  "REQUIERE", "POSTULA_A", "USA_TECNOLOGIA"]

MODOS_RUTA = {
    "Red profesional (contactos y empleos)": ["CONECTA_CON", "TRABAJA_EN", "PUBLICA"],
    "Red + proyectos": ["CONECTA_CON", "TRABAJA_EN", "PUBLICA", "PARTICIPA_EN"],
    "Cualquier relación del grafo": TIPOS_RELACION,
}

# La plantilla solo admite etiquetas/tipos de una lista blanca (Cypher no permite parametrizar etiquetas
# ni tipos de relación); los valores (ids) sí se pasan como parámetros.
Q_RUTA_PLANTILLA = """
MATCH (a:{eo} {{{ko}: $origen}}), (b:{ed} {{{kd}: $destino}})
MATCH p = {funcion}((a)-[:{tipos}*..{max}]-(b))
RETURN [n IN nodes(p) | {{etiqueta: labels(n)[0], nombre: coalesce(n.nombre, n.titulo), id: coalesce(n.id, n.nombre)}}] AS nodos,
       [r IN relationships(p) | type(r)] AS relaciones,
       length(p) AS saltos
LIMIT $limite
"""

# Ejemplo concreto (usado en la documentación): ruta más corta usuario → empresa por la red profesional
Q_RUTA_USUARIO_EMPRESA = """
MATCH (a:Usuario {id: $origen}), (b:Empresa {id: $destino})
MATCH p = shortestPath((a)-[:CONECTA_CON|TRABAJA_EN*..8]-(b))
RETURN [n IN nodes(p) | coalesce(n.nombre, n.titulo)] AS nodos, [r IN relationships(p) | type(r)] AS relaciones,
       length(p) AS saltos
"""

Q_GRADO_SEPARACION = """
MATCH (a:Usuario {id: $a}), (b:Usuario {id: $b})
OPTIONAL MATCH p = shortestPath((a)-[:CONECTA_CON*..10]-(b))
RETURN CASE WHEN p IS NULL THEN null ELSE length(p) END AS grado,
       [n IN coalesce(nodes(p), []) | n.nombre] AS ruta
"""


def contactos_en_comun(a: str, b: str) -> list[dict]:
    return leer(Q_CONTACTOS_EN_COMUN, a=a, b=b)


def estan_conectados(a: str, b: str) -> bool:
    return leer(Q_ESTAN_CONECTADOS, a=a, b=b)[0]["conectados"]


def usuarios_similares(id: str, limite: int = 10) -> list[dict]:
    return leer(Q_USUARIOS_SIMILARES, id=id, limite=int(limite))


def pares_similares(minimo: int = 3, limite: int = 20) -> list[dict]:
    return leer(Q_PARES_SIMILARES, minimo=int(minimo), limite=int(limite))


def usuarios_con_habilidades(habilidades: list[str]) -> list[dict]:
    return leer(Q_USUARIOS_CON_HABILIDAD, habilidades=list(habilidades))


def construir_consulta_ruta(etiqueta_origen: str, etiqueta_destino: str, tipos: list[str],
                            max_saltos: int = 8, todas: bool = False) -> str:
    if etiqueta_origen not in ETIQUETAS or etiqueta_destino not in ETIQUETAS:
        raise ValueError("Etiqueta no permitida.")
    tipos_ok = [t for t in tipos if t in TIPOS_RELACION]
    if not tipos_ok:
        raise ValueError("Debe elegir al menos un tipo de relación válido.")
    max_saltos = max(1, min(int(max_saltos), 12))
    return Q_RUTA_PLANTILLA.format(
        eo=etiqueta_origen, ko=ETIQUETAS[etiqueta_origen],
        ed=etiqueta_destino, kd=ETIQUETAS[etiqueta_destino],
        funcion="allShortestPaths" if todas else "shortestPath",
        tipos="|".join(tipos_ok), max=max_saltos,
    )


def ruta_mas_corta(etiqueta_origen: str, origen: str, etiqueta_destino: str, destino: str,
                   tipos: list[str] | None = None, max_saltos: int = 8, todas: bool = False,
                   limite: int = 10) -> list[dict]:
    if etiqueta_origen == etiqueta_destino and origen == destino:
        raise ValueError("El origen y el destino deben ser distintos.")
    q = construir_consulta_ruta(etiqueta_origen, etiqueta_destino, tipos or TIPOS_RELACION, max_saltos, todas)
    return leer(q, origen=origen, destino=destino, limite=int(limite))


def grado_separacion(a: str, b: str) -> dict:
    return leer(Q_GRADO_SEPARACION, a=a, b=b)[0]
