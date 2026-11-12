"""Crea (o promueve) una cuenta de administrador. La contraseña se pide de forma oculta.

Uso:
    python scripts/crear_admin.py --nombre "Nombre Apellido" --email admin@dominio.com
Si el correo ya existe, la cuenta se convierte en administrador y se le asigna la nueva contraseña.
"""
import argparse
import getpass
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from orbita import esquema, seguridad  # noqa: E402
from orbita.db import cerrar  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--nombre", required=True)
    ap.add_argument("--email", required=True)
    args = ap.parse_args()
    esquema.crear_esquema()
    print("Requisitos: 8+ caracteres, mayúscula, minúscula, número y símbolo.")
    p1 = getpass.getpass("Contraseña: ")
    p2 = getpass.getpass("Repita la contraseña: ")
    if p1 != p2:
        print("Las contraseñas no coinciden.")
        return 1
    try:
        u = seguridad.crear_admin(args.nombre, args.email, p1)
    except ValueError as e:
        print("Error:", e)
        return 1
    print(f"✔ Administrador listo: {u['nombre']} <{u['email']}> (id {u['id']})")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    finally:
        cerrar()
