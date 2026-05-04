#!/usr/bin/env python3
# Uruchomienie: python visualize.py  (oczekuje pliku *_matrices.json w katalogu results/)

import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np


CREW_COLORS = ["#E63946", "#2196F3", "#4CAF50", "#FF9800", "#9C27B0", "#00BCD4"]
BG = "#F8F9FA"
ROAD_RING_R = 1.72
CREW_RING_R = 0.52
ROAD_NODE_R = 0.175
CREW_NODE_R = 0.13


def find_all_matrices(results_dir: str = "results") -> list[Path]:
    candidates = sorted(Path(results_dir).glob("*_matrices.json"))
    if not candidates:
        sys.exit("Nie znaleziono pliku *_matrices.json w katalogu results/")
    return candidates


def circle_positions(n: int, radius: float, offset_angle: float = 0.0) -> list[tuple[float, float]]:
    angles = np.linspace(0, 2 * np.pi, n, endpoint=False) + offset_angle
    return [(radius * np.cos(a), radius * np.sin(a)) for a in angles]


def draw_graph(ax: plt.Axes, solution: dict, instance: dict, title: str) -> None:
    edge_ids = instance["edge_ids"]
    n_roads = len(edge_ids)
    n_crews = instance["crews_count"]
    matrix = solution["matrix"]
    schedule = solution["schedule"]
    crew_intervals = schedule["crew_intervals"]
    edge_starts = schedule["edge_starts"]
    edge_ends = schedule["edge_ends"]
    objective = int(solution.get("best_objective", 0))
    feasible = solution.get("feasible", False)

    active = [i for i in range(n_crews) if crew_intervals[i]]

    road_pos = circle_positions(n_roads, ROAD_RING_R, offset_angle=-np.pi / 2)
    crew_pos_list = circle_positions(
        len(active), CREW_RING_R,
        offset_angle=-np.pi / 2 + (np.pi / len(active) if len(active) > 1 else 0),
    )
    crew_pos = {ci: crew_pos_list[j] for j, ci in enumerate(active)}

    ax.set_facecolor(BG)

    ring = plt.Circle((0, 0), ROAD_RING_R, fill=False, edgecolor="#ddd", lw=1, zorder=0)
    ax.add_patch(ring)

    for crew_idx in active:
        color = CREW_COLORS[crew_idx % len(CREW_COLORS)]
        cx, cy = crew_pos[crew_idx]

        for order, (_, _, road_idx) in enumerate(crew_intervals[crew_idx]):
            rx, ry = road_pos[road_idx]

            crews_on_road = [c for c in active if matrix[c][road_idx]]
            pos_in_group = crews_on_road.index(crew_idx)
            n_group = len(crews_on_road)
            rad = 0.12 * (pos_in_group - (n_group - 1) / 2)

            ax.annotate(
                "",
                xy=(rx, ry),
                xytext=(cx, cy),
                arrowprops=dict(
                    arrowstyle="-|>",
                    color=color,
                    lw=1.6,
                    alpha=0.65,
                    connectionstyle=f"arc3,rad={rad}",
                    mutation_scale=11,
                ),
                zorder=2,
            )

            t = 0.65
            bx, by = cx + t * (rx - cx), cy + t * (ry - cy)
            ax.text(
                bx, by, str(order + 1),
                fontsize=7, ha="center", va="center",
                color=color, fontweight="bold",
                bbox=dict(boxstyle="circle,pad=0.13", fc="white", ec=color, lw=1.1, alpha=0.97),
                zorder=5,
            )

    for i, road_id in enumerate(edge_ids):
        x, y = road_pos[i]
        st, en = int(edge_starts[i]), int(edge_ends[i])
        primary = next((c for c in range(n_crews) if matrix[c][i]), None)
        border = CREW_COLORS[primary % len(CREW_COLORS)] if primary is not None else "#aaa"

        ax.add_patch(plt.Circle((x, y), ROAD_NODE_R + 0.03, color="white", zorder=3))
        ax.add_patch(plt.Circle((x, y), ROAD_NODE_R, fill=False, edgecolor=border, lw=2.4, zorder=4))

        angle = np.arctan2(y, x)
        lx = (ROAD_RING_R + ROAD_NODE_R + 0.14) * np.cos(angle)
        ly = (ROAD_RING_R + ROAD_NODE_R + 0.14) * np.sin(angle)
        ax.text(lx, ly, road_id, fontsize=8.5, ha="center", va="center",
                fontweight="bold", color="#1a1a2e", zorder=5)

        ax.text(x, y, f"{st}–{en}", fontsize=5.5, ha="center", va="center",
                color=border, fontweight="bold", zorder=5)

        n_assigned = sum(1 for c in range(n_crews) if matrix[c][i])
        if n_assigned > 1:
            ax.text(x + ROAD_NODE_R + 0.02, y + ROAD_NODE_R + 0.02,
                    f"×{n_assigned}", fontsize=6.5, ha="left", va="bottom",
                    color="#555", fontweight="bold", zorder=5)

    for crew_idx in active:
        x, y = crew_pos[crew_idx]
        color = CREW_COLORS[crew_idx % len(CREW_COLORS)]
        n_jobs = len(crew_intervals[crew_idx])
        ax.add_patch(plt.Circle((x, y), CREW_NODE_R, color=color, zorder=4))
        ax.text(x, y + 0.005, f"E{crew_idx + 1}", fontsize=8.5, ha="center", va="center",
                color="white", fontweight="bold", zorder=5)
        ax.text(x, y - CREW_NODE_R - 0.08, f"{n_jobs} rem.",
                fontsize=6.5, ha="center", va="top", color=color, zorder=5)

    pad = 0.42
    ax.set_xlim(-(ROAD_RING_R + pad), ROAD_RING_R + pad)
    ax.set_ylim(-(ROAD_RING_R + pad), ROAD_RING_R + pad)
    ax.set_aspect("equal")
    ax.axis("off")

    feas_icon = "✓" if feasible else "✗"
    feas_color = "#2e7d32" if feasible else "#c62828"
    ax.set_title(title, fontsize=13, fontweight="bold", color="#1a1a2e", pad=14)
    ax.text(0.5, 1.01, f"Makespan = {objective}  {feas_icon}",
            transform=ax.transAxes, ha="center", fontsize=9,
            color=feas_color, fontweight="bold")

    patches = [
        mpatches.Patch(
            color=CREW_COLORS[ci % len(CREW_COLORS)],
            label=f"Ekipa {ci + 1}  (k={instance['crew_costs'][ci]:.0f}/dzień)",
        )
        for ci in active
    ]
    ax.legend(handles=patches, loc="lower center",
              bbox_to_anchor=(0.5, -0.05), ncol=len(active),
              fontsize=8, framealpha=0.96, edgecolor="#ccc")


def render(path: Path) -> None:
    data = json.loads(path.read_text())
    instance = data["instance"]
    best = data["best_overall"]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(18, 9.5))
    fig.patch.set_facecolor(BG)

    draw_graph(ax1, best["ga"], instance, "Algorytm Genetyczny (GA)")
    draw_graph(ax2, best["bee"], instance, "Algorytm Pszczeli (Bee)")

    fig.suptitle("Przydział ekip do remontów dróg", fontsize=17,
                 fontweight="bold", color="#1a1a2e", y=1.00)

    note = (
        f"{len(instance['edge_ids'])} drogi  ·  {instance['crews_count']} ekip  ·  "
        f"Budżet: {instance['budget']:.0f}\n"
        "Węzły zewnętrzne = drogi  ·  Węzły wewnętrzne = ekipy  ·  "
        "Liczba na strzałce = kolejność pracy ekipy  ·  ×N = liczba ekip na drodze"
    )
    fig.text(0.5, -0.01, note, ha="center", fontsize=8.5,
             color="#666", style="italic", linespacing=1.6)

    plt.tight_layout(rect=[0, 0.03, 1, 1.00])

    stem = path.stem.replace("_matrices", "")
    out = path.parent / f"{stem}_graf.png"
    plt.savefig(out, dpi=150, bbox_inches="tight", facecolor=BG)
    print(f"Zapisano: {out}")
    plt.close(fig)


def main() -> None:
    for path in find_all_matrices():
        print(f"Wczytuję: {path}")
        render(path)
    plt.show()


if __name__ == "__main__":
    main()
