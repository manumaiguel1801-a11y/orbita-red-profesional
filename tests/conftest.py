import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from orbita.db import escribir  # noqa: E402

Q_LIMPIAR = """
MATCH (n) WHERE n.id STARTS WITH 'TEST-' OR n.nombre STARTS WITH 'TEST-' OR n.titulo STARTS WITH 'TEST-'
   OR n.email ENDS WITH '@ejemplo.test'
DETACH DELETE n
"""


@pytest.fixture()
def limpio():
    """Garantiza que no queden datos de prueba antes ni después (nunca toca datos de demostración)."""
    escribir(Q_LIMPIAR)
    yield
    escribir(Q_LIMPIAR)
