#!/usr/bin/env python3
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

CREW_COLORS = ["#E63946", "#2196F3", "#4CAF50", "#FF9800", "#9C27B0", "#00BCD4"]
BG = "#FFFFFF"


def load_matrix_data(path: Path) -> tuple[list[str], list[str], dict[str, list[list[int]]]]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    instance = raw.get("instance", {})
    best_overall = raw.get("best_overall", {})
    edge_ids = instance.get("edge_ids", [])
    crew_costs = instance.get("crew_costs", [])
    crew_labels = [f"Ekipa {i + 1} (koszt={cost:.0f})" for i, cost in enumerate(crew_costs)]
    matrices = {}
    for solver in ("ga", "bee"):
        solver_data = best_overall.get(solver, {})
        matrix = solver_data.get("matrix", [])
        if matrix:
            matrices[solver.upper()] = matrix
    return crew_labels, edge_ids, matrices


def node_positions(count: int, x: float, y_min: float, y_max: float) -> list[tuple[float, float]]:
    if count == 0:
        return []
    ys = np.linspace(y_max, y_min, count)
    return [(x, float(y)) for y in ys]


def draw_assignment_graph(ax: plt.Axes, matrix: np.ndarray, crew_labels: list[str], edge_ids: list[str], title: str) -> None:
    crews_count = matrix.shape[0]
    roads_count = matrix.shape[1]
    crew_positions = node_positions(crews_count, x=-1.0, y_min=-1.0, y_max=1.0)
    road_positions = node_positions(roads_count, x=1.0, y_min=-1.0, y_max=1.0)

    for crew_idx, (cx, cy) in enumerate(crew_positions):
        color = CREW_COLORS[crew_idx % len(CREW_COLORS)]
        ax.scatter(cx, cy, s=400, color=color, edgecolor="#333", zorder=3)
        ax.text(cx - 0.08, cy, crew_labels[crew_idx], ha="right", va="center", fontsize=9, color="#222")

    for road_idx, (rx, ry) in enumerate(road_positions):
        ax.scatter(rx, ry, s=300, facecolor="#fff", edgecolor="#444", linewidth=2, zorder=3)
        ax.text(rx + 0.08, ry, edge_ids[road_idx], ha="left", va="center", fontsize=9, color="#222")

    for crew_idx in range(crews_count):
        color = CREW_COLORS[crew_idx % len(CREW_COLORS)]
        for road_idx in range(roads_count):
            if matrix[crew_idx][road_idx] == 1:
                cx, cy = crew_positions[crew_idx]
                rx, ry = road_positions[road_idx]
                ax.plot([cx, rx], [cy, ry], color=color, linewidth=2.0, alpha=0.8, zorder=1)

    ax.set_title(title, fontsize=14, fontweight="bold")
    ax.set_xlim(-1.4, 1.4)
    ax.set_ylim(-1.15, 1.15)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.spines[["top", "right", "bottom", "left"]].set_visible(False)

    # Add legend only for crews that appear in this matrix.
    handles = []
    for crew_idx in range(matrix.shape[0]):
        color = CREW_COLORS[crew_idx % len(CREW_COLORS)]
        handles.append(plt.Line2D([0], [0], color=color, lw=4, label=crew_labels[crew_idx]))
    ax.legend(handles=handles, loc="lower center", bbox_to_anchor=(0.5, -0.15), ncol=min(3, matrix.shape[0]), fontsize=8, frameon=False)


def main() -> None:
    path = Path("results") / "results_matrices.json"
    if not path.exists():
        raise SystemExit(f"Nie znaleziono pliku: {path}")

    crew_labels, edge_ids, matrices = load_matrix_data(path)
    if not matrices:
        raise SystemExit("Brak danych macierzy w results_matrices.json")

    fig, axes = plt.subplots(1, len(matrices), figsize=(18, 7), constrained_layout=True)
    if len(matrices) == 1:
        axes = [axes]

    for ax, (solver_name, matrix) in zip(axes, matrices.items()):
        draw_assignment_graph(ax, np.array(matrix, dtype=int), crew_labels, edge_ids, f"{solver_name} - przydziały ekip")

    fig.suptitle("Graf połączeń ekip z drogami", fontsize=18, fontweight="bold")
    out_path = Path("results") / "graph_assignments.png"
    fig.savefig(out_path, dpi=200, facecolor=BG, bbox_inches="tight")
    print(f"Zapisano: {out_path}")
    plt.show()


if __name__ == "__main__":
    main()
