"""Dibuja el diagrama del modelo de grafo (docs/modelo_grafo.png)."""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyArrowPatch  # noqa: E402

RAIZ = Path(__file__).resolve().parent.parent

NODOS = {  # nombre: (x, y, color, propiedades)
    "Usuario":   (0.0, 0.0, "#2563EB", "id · nombre · email\ntitular · ciudad\naños_experiencia"),
    "Empresa":   (4.2, 1.9, "#0F766E", "id · nombre\nsector · ciudad · tamaño"),
    "Oferta":    (4.2, -1.9, "#DC2626", "id · título · modalidad\nnivel · salario · activa"),
    "Habilidad": (0.0, -3.9, "#D97706", "nombre · categoría"),
    "Proyecto":  (-4.2, -1.9, "#7C3AED", "id · nombre · estado\naño · descripción"),
}
RELS = [  # origen, destino, etiqueta, curvatura
    ("Usuario", "Usuario", "CONECTA_CON\n{desde}", 0),
    ("Usuario", "Empresa", "TRABAJA_EN\n{cargo, desde, actual}", 0.0),
    ("Usuario", "Habilidad", "TIENE_HABILIDAD\n{nivel 1-5}", 0.0),
    ("Usuario", "Proyecto", "PARTICIPA_EN\n{rol}", 0.0),
    ("Usuario", "Oferta", "POSTULA_A\n{fecha, estado}", 0.0),
    ("Empresa", "Oferta", "PUBLICA\n{fecha}", 0.0),
    ("Oferta", "Habilidad", "REQUIERE\n{nivel_minimo, obligatoria}", 0.0),
    ("Proyecto", "Habilidad", "USA_TECNOLOGIA", 0.0),
]


def main():
    fig, ax = plt.subplots(figsize=(13, 9.5))
    ax.set_xlim(-6.6, 6.6); ax.set_ylim(-5.4, 3.6); ax.set_aspect("equal"); ax.axis("off")
    R = 0.95
    for a, b, et, _ in RELS:
        (x1, y1), (x2, y2) = NODOS[a][:2], NODOS[b][:2]
        if a == b:
            ax.add_patch(FancyArrowPatch((x1 - 0.5, y1 + 0.8), (x1 + 0.5, y1 + 0.8), connectionstyle="arc3,rad=-1.6",
                                         arrowstyle="-", lw=2, color="#475569"))
            ax.text(x1, y1 + 2.05, et, ha="center", va="center", fontsize=9.5, color="#1E293B",
                    bbox=dict(boxstyle="round,pad=0.25", fc="white", ec="#CBD5E1"))
            continue
        d = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
        ux, uy = (x2 - x1) / d, (y2 - y1) / d
        ax.add_patch(FancyArrowPatch((x1 + ux * R, y1 + uy * R), (x2 - ux * R, y2 - uy * R), arrowstyle="-|>",
                                     mutation_scale=18, lw=2, color="#475569"))
        ax.text((x1 + x2) / 2, (y1 + y2) / 2, et, ha="center", va="center", fontsize=9.5, color="#1E293B",
                bbox=dict(boxstyle="round,pad=0.25", fc="white", ec="#CBD5E1"))
    for n, (x, y, c, props) in NODOS.items():
        ax.add_patch(plt.Circle((x, y), R, color=c, zorder=3))
        ax.text(x, y, n, ha="center", va="center", color="white", fontsize=12.5, fontweight="bold", zorder=4)
        dx, dy = (-2.3, 0.75) if n == "Usuario" else (0, -R - 0.45 if y <= 0 else R + 0.45)
        ax.text(x + dx, y + dy, props, ha="center", va="center", fontsize=8.5, color="#334155", zorder=4,
                bbox=dict(boxstyle="round,pad=0.3", fc="#F8FAFC", ec="#E2E8F0"))
    ax.set_title("Órbita · Modelo de grafo (property graph en Neo4j)", fontsize=15, fontweight="bold", color="#0F172A")
    out = RAIZ / "docs" / "modelo_grafo.png"
    fig.savefig(out, dpi=150, bbox_inches="tight", facecolor="white")
    print(out)


if __name__ == "__main__":
    main()
