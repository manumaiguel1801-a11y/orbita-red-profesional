"""Genera los scripts .cypher entregables a partir del código fuente (fuente única de verdad).

    cypher/01_esquema.cypher        restricciones de unicidad e índices
    cypher/02_datos_demo.cypher     carga de datos de demostración (MERGE, idempotente)
    cypher/03_consultas.cypher      todas las consultas parametrizadas que usa la aplicación
"""
import sys
import textwrap
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from orbita import analitica, catalogo, datos_demo, esquema, grafo_visual, recomendaciones, red, seguridad, usuarios  # noqa: E402

SECCIONES = [
    ("CRUD de usuarios y vínculos", usuarios),
    ("Empresas, habilidades, proyectos y ofertas", catalogo),
    ("Red: contactos en común, similitud y rutas más cortas", red),
    ("Recomendaciones", recomendaciones),
    ("Analítica", analitica),
    ("Visualización", grafo_visual),
    ("Administración", esquema),
    ("Autenticación, sesiones y roles", seguridad),
]


def main():
    out = RAIZ / "cypher"
    out.mkdir(exist_ok=True)
    (out / "01_esquema.cypher").write_text(
        "// Esquema de Órbita: restricciones de unicidad e índices\n\n"
        + "\n".join(q + ";" for q in esquema.RESTRICCIONES) + "\n\n"
        + "\n".join(q + ";" for q in esquema.INDICES) + "\n", encoding="utf-8")
    (out / "02_datos_demo.cypher").write_text(datos_demo.script_cypher(), encoding="utf-8")

    partes = ["// Consultas Cypher de Órbita (extraídas automáticamente del código de la aplicación).",
              "// Los valores con $ son parámetros enviados por el controlador de Neo4j (nunca concatenados).", ""]
    for titulo, modulo in SECCIONES:
        partes += ["", "// " + "=" * 76, f"// {titulo}  ({modulo.__name__})", "// " + "=" * 76]
        for nombre, valor in vars(modulo).items():
            if nombre.startswith("Q_") and isinstance(valor, str):
                partes += ["", f"// ---- {nombre}", textwrap.dedent(valor).strip() + ";"]
    partes += ["", "// ---- Q_RUTA (ejemplo generado: usuario → empresa por la red profesional)",
               red.construir_consulta_ruta("Usuario", "Empresa", ["CONECTA_CON", "TRABAJA_EN"], 8).strip() + ";"]
    (out / "03_consultas.cypher").write_text("\n".join(partes) + "\n", encoding="utf-8")
    for f in sorted(out.glob("*.cypher")):
        print(f"{f.relative_to(RAIZ)}  ({f.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
