"""Inicializa Neo4j: crea restricciones/índices y carga los datos de demostración.

Uso:
    python scripts/inicializar_bd.py                 # solo si la base está vacía
    python scripts/inicializar_bd.py --actualizar    # base con datos: MERGE idempotente (no borra nada)
    python scripts/inicializar_bd.py --reemplazar    # muestra el contenido, pide escribir BORRAR y recarga
    python scripts/inicializar_bd.py --solo-esquema  # solo restricciones e índices
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from orbita import esquema, datos_demo  # noqa: E402
from orbita.db import cerrar  # noqa: E402


def mostrar_contenido() -> int:
    total = esquema.total_nodos()
    print(f"Nodos actuales: {total}")
    for k, v in esquema.conteo_nodos().items():
        print(f"   {k:<10} {v}")
    for k, v in esquema.conteo_relaciones().items():
        print(f"   {k:<16} {v}")
    return total


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--actualizar", action="store_true")
    g.add_argument("--reemplazar", action="store_true")
    g.add_argument("--solo-esquema", action="store_true")
    args = ap.parse_args()

    print("1) Creando restricciones e índices...")
    for nombre in esquema.crear_esquema():
        print("   ✔", nombre)
    if args.solo_esquema:
        return 0

    print("2) Contenido actual de la base:")
    total = mostrar_contenido()

    if total and args.reemplazar:
        print("\n⚠  Se eliminará TODO el contenido mostrado arriba. Esta acción no se puede deshacer.")
        if input("Escriba BORRAR para confirmar: ").strip() != "BORRAR":
            print("Cancelado. No se eliminó nada.")
            return 1
        esquema.borrar_todo("BORRAR")
        print("   Base vaciada.")
    elif total and not args.actualizar:
        print("\nLa base ya contiene datos. No se modificó nada.\n"
              "Use --actualizar (MERGE sin borrar) o --reemplazar (borrado con confirmación).")
        return 1

    print("3) Cargando datos de demostración...")
    for clave, n in datos_demo.cargar().items():
        print(f"   ✔ {clave:<12} {n}")
    print("4) Contenido final:")
    mostrar_contenido()
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    finally:
        cerrar()
