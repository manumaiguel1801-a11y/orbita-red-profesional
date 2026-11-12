"""Verifica la conexión con Neo4j AuraDB y muestra el contenido actual (sin modificar nada)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from orbita.db import leer, get_driver, cerrar  # noqa: E402

if __name__ == "__main__":
    drv = get_driver()
    info = leer("CALL dbms.components() YIELD name, versions, edition RETURN name, versions[0] AS version, edition")
    print("Conexión OK:", info)
    print("Nodos por etiqueta:")
    for r in leer("MATCH (n) RETURN labels(n) AS etiquetas, count(*) AS total ORDER BY total DESC"):
        print("  ", r)
    print("Relaciones por tipo:")
    for r in leer("MATCH ()-[r]->() RETURN type(r) AS tipo, count(*) AS total ORDER BY total DESC"):
        print("  ", r)
    try:
        print("GDS:", leer("RETURN gds.version() AS v"))
    except Exception as e:  # AuraDB Free no incluye GDS
        print("GDS no disponible:", type(e).__name__)
    cerrar()
