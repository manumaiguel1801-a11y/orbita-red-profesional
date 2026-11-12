"""Panel de analítica: usuarios influyentes, comunidades y habilidades demandadas.

AuraDB Free NO incluye la librería Graph Data Science (GDS), por lo que:
- La centralidad de grado y las métricas de demanda se calculan directamente en Cypher.
- PageRank, intermediación (betweenness) y comunidades se calculan con NetworkX sobre el
  subgrafo CONECTA_CON extraído de Neo4j con Cypher en el momento de la consulta
  (los datos siempre son los reales y actuales de la base).

Comunidades:
- Componentes conectados: dos usuarios están en el mismo componente si existe un camino
  de conexiones entre ellos. Es exacto pero grueso: una red bien conectada forma un solo componente.
- Louvain (networkx.community.louvain_communities, semilla fija 42 => reproducible):
  maximiza la modularidad, agrupando usuarios con más conexiones internas que externas.
  Limitaciones: heurístico (no garantiza el óptimo global), puede variar con otra semilla,
  tiene límite de resolución (puede fusionar comunidades pequeñas), ignora pesos y el resto
  de relaciones (habilidades, empresas) y escala en memoria del servidor de la aplicación.
"""
from __future__ import annotations

import networkx as nx

from .db import leer, escribir

# ---------------------------------------------------------------- Influencia (A17)
Q_CENTRALIDAD_GRADO = """
MATCH (u:Usuario)
OPTIONAL MATCH (u)-[:TRABAJA_EN {actual: true}]->(e:Empresa)
RETURN u.id AS id, u.nombre AS nombre, u.titular AS titular, collect(e.nombre)[0] AS empresa,
       COUNT { (u)-[:CONECTA_CON]-(:Usuario) } AS conexiones,
       COUNT { (u)-[:CONECTA_CON]-(:Usuario)-[:CONECTA_CON]-(x:Usuario) WHERE x <> u } AS alcance_2_saltos,
       COUNT { (u)-[:PARTICIPA_EN]->(:Proyecto) } AS proyectos
ORDER BY conexiones DESC, nombre
"""

Q_ARISTAS_CONEXION = """
MATCH (a:Usuario)-[:CONECTA_CON]->(b:Usuario)
RETURN a.id AS origen, b.id AS destino
"""

Q_NODOS_USUARIO = "MATCH (u:Usuario) RETURN u.id AS id, u.nombre AS nombre, u.titular AS titular, u.ciudad AS ciudad"

Q_GUARDAR_COMUNIDAD = """
UNWIND $filas AS fila
MATCH (u:Usuario {id: fila.id})
SET u.comunidad = fila.comunidad
RETURN count(u) AS actualizados
"""

# ---------------------------------------------------------------- Demanda de habilidades (B6, A19)
Q_HABILIDADES_DEMANDADAS = """
MATCH (o:Oferta)-[r:REQUIERE]->(h:Habilidad)
WHERE ($solo_activas = false OR coalesce(o.activa, true))
WITH h, count(DISTINCT o) AS ofertas, sum(CASE WHEN r.obligatoria THEN 1 ELSE 0 END) AS obligatoria_en
RETURN h.nombre AS habilidad, h.categoria AS categoria, ofertas, obligatoria_en,
       COUNT { (h)<-[:TIENE_HABILIDAD]-(:Usuario) } AS profesionales_que_la_tienen,
       COUNT { (h)<-[:USA_TECNOLOGIA]-(:Proyecto) } AS proyectos_que_la_usan
ORDER BY ofertas DESC, obligatoria_en DESC, habilidad
LIMIT $limite
"""

Q_DEMANDA_POR_CATEGORIA = """
MATCH (o:Oferta)-[:REQUIERE]->(h:Habilidad)
WHERE coalesce(o.activa, true)
RETURN h.categoria AS categoria, count(*) AS requerimientos, count(DISTINCT o) AS ofertas
ORDER BY requerimientos DESC
"""

Q_EMPRESAS_ACTIVAS = """
MATCH (e:Empresa)
RETURN e.nombre AS empresa, e.sector AS sector,
       COUNT { (e)-[:PUBLICA]->(:Oferta) } AS ofertas,
       COUNT { (e)-[:PUBLICA]->(:Oferta)<-[:POSTULA_A]-(:Usuario) } AS postulaciones,
       COUNT { (e)<-[:TRABAJA_EN {actual: true}]-(:Usuario) } AS empleados
ORDER BY postulaciones DESC, ofertas DESC
"""

Q_RESUMEN = """
RETURN COUNT { (:Usuario) } AS usuarios, COUNT { (:Empresa) } AS empresas,
       COUNT { (:Habilidad) } AS habilidades, COUNT { (:Proyecto) } AS proyectos,
       COUNT { (o:Oferta) WHERE coalesce(o.activa, true) } AS ofertas_activas,
       COUNT { ()-[:CONECTA_CON]->() } AS conexiones,
       COUNT { ()-[:POSTULA_A]->() } AS postulaciones,
       COUNT { ()-[]->() } AS relaciones
"""

Q_USUARIOS_POR_CIUDAD = "MATCH (u:Usuario) RETURN coalesce(u.ciudad, 'Sin ciudad') AS ciudad, count(*) AS usuarios ORDER BY usuarios DESC"


def resumen() -> dict:
    return leer(Q_RESUMEN)[0]


def centralidad_grado() -> list[dict]:
    return leer(Q_CENTRALIDAD_GRADO)


def grafo_conexiones() -> nx.Graph:
    g = nx.Graph()
    for n in leer(Q_NODOS_USUARIO):
        g.add_node(n["id"], **n)
    g.add_edges_from((r["origen"], r["destino"]) for r in leer(Q_ARISTAS_CONEXION))
    return g


def pagerank(g: nx.Graph, d: float = 0.85, iteraciones: int = 100, tolerancia: float = 1e-10) -> dict:
    """PageRank por iteración de potencias (grafo no dirigido).

    PR(v) = (1-d)/N + d · Σ_{u ∈ vecinos(v)} PR(u)/grado(u)
    La masa de los nodos sin conexiones se redistribuye uniformemente.
    """
    n = g.number_of_nodes()
    if n == 0:
        return {}
    pr = {v: 1.0 / n for v in g}
    for _ in range(iteraciones):
        colgantes = sum(pr[v] for v in g if g.degree(v) == 0)
        nuevo = {v: (1 - d) / n + d * (colgantes / n + sum(pr[u] / g.degree(u) for u in g.neighbors(v))) for v in g}
        if sum(abs(nuevo[v] - pr[v]) for v in g) < tolerancia:
            pr = nuevo
            break
        pr = nuevo
    return pr


def usuarios_influyentes(limite: int = 10) -> list[dict]:
    """Combina grado (Cypher) con PageRank e intermediación (betweenness) sobre CONECTA_CON."""
    g = grafo_conexiones()
    if g.number_of_nodes() == 0:
        return []
    pr = pagerank(g)
    bt = nx.betweenness_centrality(g, normalized=True)
    filas = []
    for f in centralidad_grado():
        f["pagerank"] = round(pr.get(f["id"], 0.0), 4)
        f["intermediacion"] = round(bt.get(f["id"], 0.0), 4)
        filas.append(f)
    # índice de influencia: promedio de las tres métricas normalizadas a [0,1]
    for clave in ("conexiones", "pagerank", "intermediacion"):
        mx = max((f[clave] for f in filas), default=0) or 1
        for f in filas:
            f[f"_{clave}"] = f[clave] / mx
    for f in filas:
        f["indice_influencia"] = round(100 * (f.pop("_conexiones") + f.pop("_pagerank") + f.pop("_intermediacion")) / 3, 1)
    filas.sort(key=lambda f: (-f["indice_influencia"], f["nombre"]))
    return filas[:limite]


def comunidades(metodo: str = "louvain", semilla: int = 42) -> list[dict]:
    """Devuelve [{id, nombre, titular, ciudad, comunidad}] con comunidades numeradas desde 1 (mayor primero)."""
    g = grafo_conexiones()
    if g.number_of_nodes() == 0:
        return []
    if metodo == "componentes":
        grupos = list(nx.connected_components(g))
    else:
        grupos = nx.community.louvain_communities(g, seed=semilla)
    grupos = sorted(grupos, key=lambda s: (-len(s), min(s)))
    filas = []
    for i, grupo in enumerate(grupos, start=1):
        for nid in sorted(grupo):
            d = g.nodes[nid]
            filas.append({"id": nid, "nombre": d.get("nombre"), "titular": d.get("titular"),
                          "ciudad": d.get("ciudad"), "comunidad": i})
    return filas


def modularidad(filas: list[dict]) -> float:
    g = grafo_conexiones()
    if g.number_of_edges() == 0:
        return 0.0
    grupos: dict[int, set] = {}
    for f in filas:
        grupos.setdefault(f["comunidad"], set()).add(f["id"])
    return round(nx.community.modularity(g, grupos.values()), 4)


def resumen_comunidades(filas: list[dict]) -> list[dict]:
    """Para cada comunidad: tamaño, miembros, habilidades y empresas predominantes (consultadas en Neo4j)."""
    grupos: dict[int, list[str]] = {}
    for f in filas:
        grupos.setdefault(f["comunidad"], []).append(f["id"])
    q = """
    MATCH (u:Usuario) WHERE u.id IN $ids
    WITH collect(u) AS miembros
    RETURN [u IN miembros | u.nombre] AS nombres,
      COLLECT { UNWIND miembros AS u MATCH (u)-[:TIENE_HABILIDAD]->(h)
                WITH h.nombre AS h, count(*) AS c ORDER BY c DESC, h LIMIT 4
                RETURN h + ' (' + toString(c) + ')' } AS habilidades,
      COLLECT { UNWIND miembros AS u MATCH (u)-[:TRABAJA_EN {actual: true}]->(e)
                WITH e.nombre AS e, count(*) AS c ORDER BY c DESC, e LIMIT 3
                RETURN e + ' (' + toString(c) + ')' } AS empresas,
      COLLECT { UNWIND miembros AS u WITH u.ciudad AS ciudad, count(*) AS c ORDER BY c DESC, ciudad LIMIT 1
                RETURN ciudad } AS ciudad
    """
    out = []
    for cid, ids in sorted(grupos.items()):
        r = leer(q, ids=ids)[0]
        out.append({"comunidad": cid, "tamano": len(ids), "miembros": r["nombres"],
                    "habilidades_predominantes": r["habilidades"], "empresas_predominantes": r["empresas"],
                    "ciudad_predominante": (r["ciudad"] or [None])[0]})
    return out


def guardar_comunidades(filas: list[dict]) -> int:
    """Persiste la comunidad detectada como propiedad u.comunidad (acción explícita del usuario)."""
    return escribir(Q_GUARDAR_COMUNIDAD, filas=[{"id": f["id"], "comunidad": f["comunidad"]} for f in filas])[0]["actualizados"]


def habilidades_demandadas(limite: int = 15, solo_activas: bool = True) -> list[dict]:
    return leer(Q_HABILIDADES_DEMANDADAS, limite=int(limite), solo_activas=solo_activas)


def demanda_por_categoria() -> list[dict]:
    return leer(Q_DEMANDA_POR_CATEGORIA)


def empresas_activas() -> list[dict]:
    return leer(Q_EMPRESAS_ACTIVAS)


def usuarios_por_ciudad() -> list[dict]:
    return leer(Q_USUARIOS_POR_CIUDAD)
