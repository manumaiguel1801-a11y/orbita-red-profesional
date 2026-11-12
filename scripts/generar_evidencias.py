"""Ejecuta las consultas clave contra Neo4j AuraDB y guarda los resultados reales en docs/evidencias.md."""
import subprocess
import sys
from datetime import datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from orbita import analitica as an  # noqa: E402
from orbita import esquema, red  # noqa: E402
from orbita import recomendaciones as rec  # noqa: E402
from orbita.db import cerrar, leer  # noqa: E402


def md_tabla(filas, columnas=None, maximo=10):
    if not filas:
        return "_Sin resultados._\n"
    columnas = columnas or list(filas[0])
    fmt = lambda v: ", ".join(map(str, v)) if isinstance(v, list) else ("" if v is None else str(v))  # noqa: E731
    out = ["| " + " | ".join(columnas) + " |", "|" + "---|" * len(columnas)]
    out += ["| " + " | ".join(fmt(f.get(c)).replace("|", "/") for c in columnas) + " |" for f in filas[:maximo]]
    return "\n".join(out) + "\n"


def ruta_txt(r):
    s = r["nodos"][0]["nombre"]
    for rel, n in zip(r["relaciones"], r["nodos"][1:]):
        s += f" -[{rel}]- {n['nombre']} ({n['etiqueta']})"
    return s


def nombre(uid):
    return leer("MATCH (u:Usuario {id:$id}) RETURN u.nombre AS n", id=uid)[0]["n"]


def main():
    L = [f"# Evidencias de funcionamiento\n",
         f"Generado automáticamente por `scripts/generar_evidencias.py` el {datetime.now():%Y-%m-%d %H:%M} "
         f"ejecutando las consultas **contra la instancia real de Neo4j AuraDB**.\n"]
    v = leer("CALL dbms.components() YIELD name, versions, edition RETURN name, versions[0] AS version, edition")
    L.append(f"**Servidor:** {v[0]['name']} {v[0]['version']} ({v[0]['edition']})\n")
    L.append("## Contenido de la base\n")
    L.append(md_tabla([{"Etiqueta": k, "Nodos": n} for k, n in esquema.conteo_nodos().items()]))
    L.append(md_tabla([{"Relación": k, "Total": n} for k, n in esquema.conteo_relaciones().items()]))
    L.append("## Restricciones de unicidad\n")
    L.append(md_tabla(esquema.listar_restricciones(), ["name", "labelsOrTypes", "properties", "type"]))

    L.append("## 1. ¿Qué usuarios tienen habilidades similares?\n")
    L.append(f"Similares a **{nombre('U001')}** (Jaccard):\n")
    L.append(md_tabla(red.usuarios_similares("U001", 5), ["nombre", "compartidas", "en_comun", "jaccard", "ya_conectados"]))
    L.append("Pares más similares de toda la red:\n")
    L.append(md_tabla(red.pares_similares(3, 5), ["usuario_a", "usuario_b", "compartidas", "jaccard"]))

    L.append("## 2. ¿Qué contactos en común existen entre dos profesionales?\n")
    L.append(f"Entre **{nombre('U001')}** y **{nombre('U009')}**:\n")
    L.append(md_tabla(red.contactos_en_comun("U001", "U009"), ["nombre", "titular", "conexiones"]))

    L.append("## 3. ¿Cuál es la ruta más corta entre un usuario y una empresa?\n")
    for uid, eid, modo in [("U008", "E08", "Red profesional (contactos y empleos)"), ("U043", "E01", "Cualquier relación del grafo"),
                           ("U041", "E01", "Red profesional (contactos y empleos)")]:
        rutas = red.ruta_mas_corta("Usuario", uid, "Empresa", eid, red.MODOS_RUTA[modo])
        emp = leer("MATCH (e:Empresa {id:$id}) RETURN e.nombre AS n", id=eid)[0]["n"]
        L.append(f"- **{nombre(uid)} → {emp}** ({modo}): "
                 + (f"{rutas[0]['saltos']} saltos: `{ruta_txt(rutas[0])}`" if rutas else "sin ruta (componentes distintos)") + "\n")
    rutas = red.ruta_mas_corta("Usuario", "U022", "Oferta", "O13", red.MODOS_RUTA["Red profesional (contactos y empleos)"], todas=True)
    L.append(f"\nTodas las rutas mínimas de **{nombre('U022')}** a la oferta **Arquitecto Cloud** ({len(rutas)} rutas de {rutas[0]['saltos']} saltos):\n")
    L += [f"{i}. `{ruta_txt(r)}`\n" for i, r in enumerate(rutas[:5], 1)]

    L.append("\n## 4. ¿Qué candidatos podrían recomendarse para una oferta según sus conexiones y competencias?\n")
    for oid in ["O21", "O01"]:
        t = leer("MATCH (e)-[:PUBLICA]->(o:Oferta {id:$id}) RETURN o.titulo + ' · ' + e.nombre AS t", id=oid)[0]["t"]
        L.append(f"Oferta **{t}**:\n")
        L.append(md_tabla(rec.recomendar_candidatos(oid, 6), ["nombre", "puntaje", "cobertura_pct", "cumple", "faltan",
                                                              "contactos_en_empresa", "contactos_2do_grado", "ya_postulado"]))

    L.append("## 5. ¿Qué proyectos comparten tecnologías o miembros relacionados?\n")
    L.append(md_tabla(rec.pares_proyectos_relacionados(8), ["proyecto_a", "proyecto_b", "tecnologias_compartidas",
                                                             "miembros_compartidos", "pares_conectados", "puntaje"]))

    L.append("## 6. ¿Qué habilidades son las más demandadas en las ofertas?\n")
    L.append(md_tabla(an.habilidades_demandadas(10), ["habilidad", "categoria", "ofertas", "obligatoria_en", "profesionales_que_la_tienen"]))

    L.append("## Recomendaciones de contactos, empleos y colaboradores\n")
    L.append(f"Contactos para **{nombre('U008')}**:\n")
    L.append(md_tabla(rec.recomendar_contactos("U008", 5), ["nombre", "puntaje", "comunes", "habilidades_compartidas", "empresa_compartida"]))
    L.append(f"Empleos para **{nombre('U043')}** (sin conexiones: solo pesa la cobertura de habilidades):\n")
    L.append(md_tabla(rec.recomendar_empleos("U043", 5), ["oferta", "empresa", "puntaje", "cobertura_pct", "cumple", "faltan"]))
    L.append(f"Empleos para **{nombre('U020')}**:\n")
    L.append(md_tabla(rec.recomendar_empleos("U020", 5), ["oferta", "empresa", "puntaje", "cobertura_pct", "contactos_en_empresa", "contactos_2do_grado"]))
    L.append(f"Colaboradores para **{nombre('U001')}**:\n")
    L.append(md_tabla(rec.recomendar_colaboradores("U001", 5), ["nombre", "puntaje", "tecnologias_que_aporta", "conectado", "contactos_en_comun"]))

    L.append("## Panel de analítica\n### Usuarios más influyentes\n")
    L.append(md_tabla(an.usuarios_influyentes(8), ["nombre", "conexiones", "pagerank", "intermediacion", "indice_influencia"]))
    for metodo in ["louvain", "componentes"]:
        filas = an.comunidades(metodo)
        L.append(f"### Comunidades — {metodo} (modularidad = {an.modularidad(filas)})\n")
        L.append(md_tabla(an.resumen_comunidades(filas), ["comunidad", "tamano", "ciudad_predominante",
                                                           "habilidades_predominantes", "empresas_predominantes"]))

    L.append("## Resultado de las pruebas automáticas\n")
    r = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:warnings", "tests"], cwd=RAIZ,
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    L.append("```\n" + "\n".join(r.stdout.strip().splitlines()[-3:]) + "\n```\n")
    (RAIZ / "docs" / "evidencias.md").write_text("\n".join(L), encoding="utf-8")
    print("docs/evidencias.md generado;", r.stdout.strip().splitlines()[-1])


if __name__ == "__main__":
    try:
        main()
    finally:
        cerrar()
