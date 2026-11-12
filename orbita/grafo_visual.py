"""Visualización interactiva del grafo (vis.js mediante PyVis) con datos consultados en Neo4j."""
from __future__ import annotations

from pyvis.network import Network

from .db import leer

COLORES = {
    "Usuario": "#8B5CF6", "Empresa": "#22D3EE", "Habilidad": "#A3E635",
    "Proyecto": "#F472B6", "Oferta": "#FB923C",
}
FORMAS = {"Usuario": "dot", "Empresa": "square", "Habilidad": "triangle", "Proyecto": "diamond", "Oferta": "star"}
PALETA_COMUNIDADES = ["#8B5CF6", "#A3E635", "#22D3EE", "#F472B6", "#FB923C", "#FACC15", "#2DD4BF", "#818CF8", "#A1A1AA"]

_NODO = """{id: elementId(%(v)s), etiqueta: labels(%(v)s)[0], nombre: coalesce(%(v)s.nombre, %(v)s.titulo),
  clave: coalesce(%(v)s.id, %(v)s.nombre), detalle: coalesce(%(v)s.titular, %(v)s.sector, %(v)s.categoria, %(v)s.estado, %(v)s.modalidad, '')}"""

Q_SUBGRAFO = """
MATCH (a)-[r]->(b)
WHERE type(r) IN $tipos AND labels(a)[0] IN $etiquetas AND labels(b)[0] IN $etiquetas
RETURN %s AS a, type(r) AS tipo, %s AS b
LIMIT $limite
""" % (_NODO % {"v": "a"}, _NODO % {"v": "b"})

# El número de saltos no es parametrizable en Cypher; solo se admiten 1 o 2 (lista blanca).
Q_EGO = """
MATCH (centro {%(clave)s: $clave}) WHERE $etiqueta IN labels(centro)
MATCH (centro)-[*1..%(saltos)d]-(x)
WITH centro, collect(DISTINCT x)[..$max_nodos] + [centro] AS nodos
UNWIND nodos AS a
MATCH (a)-[r]->(b) WHERE b IN nodos
RETURN %(na)s AS a, type(r) AS tipo, %(nb)s AS b
"""


def subgrafo(etiquetas: list[str], tipos: list[str], limite: int = 400) -> list[dict]:
    return leer(Q_SUBGRAFO, etiquetas=etiquetas, tipos=tipos, limite=int(limite))


def ego(etiqueta: str, clave: str, saltos: int = 1, max_nodos: int = 80) -> list[dict]:
    if etiqueta not in COLORES:
        raise ValueError("Etiqueta no permitida")
    q = Q_EGO % {"clave": "nombre" if etiqueta == "Habilidad" else "id", "saltos": 2 if saltos >= 2 else 1,
                 "na": _NODO % {"v": "a"}, "nb": _NODO % {"v": "b"}}
    return leer(q, etiqueta=etiqueta, clave=clave, max_nodos=int(max_nodos))


def filas_desde_ruta(ruta: dict) -> list[dict]:
    """Convierte el resultado de red.ruta_mas_corta en aristas para dibujar."""
    nodos, rels = ruta["nodos"], ruta["relaciones"]
    out = []
    for i, tipo in enumerate(rels):
        a, b = nodos[i], nodos[i + 1]
        out.append({"a": {"id": f"{a['etiqueta']}:{a['id']}", "etiqueta": a["etiqueta"], "nombre": a["nombre"], "clave": a["id"], "detalle": ""},
                    "tipo": tipo,
                    "b": {"id": f"{b['etiqueta']}:{b['id']}", "etiqueta": b["etiqueta"], "nombre": b["nombre"], "clave": b["id"], "detalle": ""}})
    return out


def html(filas: list[dict], altura: int = 620, comunidades: dict | None = None, resaltar: set | None = None,
         fisica: bool = True) -> str:
    """Genera el HTML interactivo. comunidades: {clave_usuario: n} para colorear por comunidad."""
    net = Network(height=f"{altura}px", width="100%", bgcolor="#0B0B0E", font_color="#E4E4E7",
                  cdn_resources="remote", directed=True)
    vistos = set()
    grados: dict[str, int] = {}
    for f in filas:
        for lado in ("a", "b"):
            grados[f[lado]["id"]] = grados.get(f[lado]["id"], 0) + 1
    for f in filas:
        for lado in ("a", "b"):
            n = f[lado]
            if n["id"] in vistos:
                continue
            vistos.add(n["id"])
            color = COLORES.get(n["etiqueta"], "#A1A1AA")
            if comunidades and n["etiqueta"] == "Usuario" and n["clave"] in comunidades:
                color = PALETA_COMUNIDADES[(comunidades[n["clave"]] - 1) % len(PALETA_COMUNIDADES)]
            borde = "#FAFAFA" if resaltar and n["clave"] in resaltar else color
            net.add_node(n["id"], label=n["nombre"] or n["clave"], shape=FORMAS.get(n["etiqueta"], "dot"),
                         color={"background": color, "border": borde, "highlight": {"background": color, "border": "#FAFAFA"}},
                         borderWidth=4 if resaltar and n["clave"] in resaltar else 1,
                         size=10 + min(grados.get(n["id"], 1), 15) * 1.6,
                         title=f"{n['etiqueta']}: {n['nombre']}\n{n.get('detalle') or ''}\nid: {n['clave']}")
        net.add_edge(f["a"]["id"], f["b"]["id"], label=f["tipo"] if len(filas) <= 60 else "", title=f["tipo"],
                     color={"color": "#3F3F46", "highlight": "#A78BFA", "hover": "#A78BFA"}, arrows="to" if f["tipo"] != "CONECTA_CON" else "",
                     font={"size": 9, "color": "#A1A1AA", "strokeWidth": 0})
    net.set_options("""
    {"physics": {"enabled": %s, "solver": "forceAtlas2Based",
                 "forceAtlas2Based": {"gravitationalConstant": -60, "springLength": 110, "avoidOverlap": 0.4},
                 "stabilization": {"iterations": 250}},
     "interaction": {"hover": true, "navigationButtons": true, "keyboard": true, "tooltipDelay": 120},
     "nodes": {"font": {"size": 13, "face": "Inter, Segoe UI, sans-serif", "color": "#E4E4E7"},
               "shadow": {"enabled": true, "color": "rgba(139,92,246,0.55)", "size": 16, "x": 0, "y": 0}},
     "edges": {"smooth": {"type": "continuous"}, "width": 1.2}}
    """ % ("true" if fisica else "false"))
    tema = ("<style>html,body{margin:0;background:#0B0B0E}.card{background:#0B0B0E!important;border:0!important}"
            "#mynetwork{border:1px solid #26262B!important;border-radius:16px;background:radial-gradient(600px 300px at 80% 0%,"
            "rgba(139,92,246,.12),transparent 60%),#0B0B0E!important}"
            "div.vis-network div.vis-navigation div.vis-button{filter:invert(.85) hue-rotate(180deg);opacity:.6}"
            "div.vis-tooltip{background:#18181B!important;color:#FAFAFA!important;border:1px solid #8B5CF6!important;"
            "border-radius:10px!important;font-family:Inter,Segoe UI,sans-serif!important;white-space:pre-line}</style></head>")
    return net.generate_html(notebook=False).replace("</head>", tema, 1)
