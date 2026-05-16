#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from time import perf_counter

import matplotlib.pyplot as plt
import numpy as np

from src.bee import BeeConfig, solve_bee
from src.ga import GAConfig, solve_ga
from src.instances import generate_instance
from visualize_graph import draw_assignment_graph


def save_instance(graph_path: Path, instance_data: dict) -> None:
    graph_path.write_text(json.dumps(instance_data, indent=2), encoding="utf-8")


def save_results_csv(csv_path: Path, rows: list[dict[str, object]]) -> None:
    with csv_path.open("w", encoding="utf-8", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def save_history(history_path: Path, graph_file: str, repetitions: int, iterations: int, runs: list[dict]) -> None:
    history_path.write_text(
        json.dumps({"graph_file": graph_file, "repetitions": repetitions, "iterations": iterations, "runs": runs}, indent=2),
        encoding="utf-8",
    )


def save_matrices(matrices_path: Path, graph_file: str, repetitions: int, iterations: int, instance: dict, best_overall: dict, runs: list[dict]) -> None:
    matrices_path.write_text(
        json.dumps(
            {
                "graph_file": graph_file,
                "repetitions": repetitions,
                "iterations": iterations,
                "instance": instance,
                "best_overall": best_overall,
                "runs": runs,
            },
            indent=2,
        ),
        encoding="utf-8",
    )


def render_graph(matrices_path: Path, output_path: Path) -> None:
    with matrices_path.open(encoding="utf-8") as handle:
        data = json.load(handle)

    instance = data["instance"]
    best_overall = data["best_overall"]
    edge_ids = instance["edge_ids"]
    crew_costs = instance["crew_costs"]
    crew_labels = [f"Ekipa {i + 1} (koszt={cost:.0f})" for i, cost in enumerate(crew_costs)]

    fig, axes = plt.subplots(1, len(best_overall), figsize=(16, 7), constrained_layout=True)
    if len(best_overall) == 1:
        axes = [axes]

    for ax, (solver_name, solver_data) in zip(axes, best_overall.items()):
        matrix = np.array(solver_data["matrix"], dtype=int)
        draw_assignment_graph(ax, matrix, crew_labels, edge_ids, f"{solver_name} - przydziały")

    fig.suptitle("Przykład wizualizacji grafu przydziału ekip", fontsize=18, fontweight="bold")
    fig.savefig(output_path, dpi=200, bbox_inches="tight")
    print(f"Zapisano wykres do: {output_path}")
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description="Przykład eksperymentu i wizualizacji dla BO")
    parser.add_argument("--graph", default="results/example_graph.json", help="Ścieżka do zapisu instancji JSON")
    parser.add_argument("--edges", type=int, default=100, help="Liczba dróg w instancji")
    parser.add_argument("--crews", type=int, default=30, help="Liczba ekip w instancji")
    parser.add_argument("--iterations", type=int, default=80, help="Liczba iteracji dla solverów")
    parser.add_argument("--repetitions", type=int, default=1, help="Liczba powtórzeń eksperymentu")
    args = parser.parse_args()

    results_dir = Path("results")
    results_dir.mkdir(exist_ok=True)

    instance = generate_instance(
        edges_count=args.edges,
        crews_count=args.crews,
        seed=1234,
        base_time_range=(5, 18),
        load_range=(2, 12),
        crew_cost_range=(5, 12),
        budget_ratio=0.6,
    )
    graph_path = Path(args.graph)
    save_instance(graph_path, {
        "edges": [
            {"id": f"e{i + 1}", "base_time": int(instance.base_times[i]), "load": float(instance.loads[i])}
            for i in range(instance.edges_count)
        ],
        "crew_costs": [float(cost) for cost in instance.crew_costs],
        "budget": float(instance.budget),
    })

    rows = []
    history_runs = []
    matrix_runs = []

    for rep in range(args.repetitions):
        print(f"Uruchamiam powtórzenie {rep + 1}/{args.repetitions}")

        ga_result = solve_ga(
            instance,
            GAConfig(population_size=30, generations=args.iterations, crossover_rate=0.8, mutation_rate=0.05, seed=1000 + rep),
        )
        bee_result = solve_bee(
            instance,
            BeeConfig(colony_size=30, iterations=args.iterations, limit=15, neighborhood_flips=2, seed=2000 + rep),
        )

        for solver_name, result in (("GA", ga_result), ("Bee", bee_result)):
            rows.append({
                "rep": rep,
                "solver": solver_name,
                "best_fitness": round(result.best_fitness, 4),
                "best_objective": round(result.best_objective, 4),
                "feasible": int(result.feasible),
                "time_s": round(result.elapsed_s, 4),
            })

        history_runs.append({
            "rep": rep,
            "ga": {"history_best_fitness": ga_result.history},
            "bee": {"history_best_fitness": bee_result.history},
        })

        matrix_runs.append({
            "rep": rep,
            "ga": {
                "best_fitness": ga_result.best_fitness,
                "best_objective": ga_result.best_objective,
                "feasible": ga_result.feasible,
                "time_s": ga_result.elapsed_s,
                "overlaps_count": ga_result.overlaps_count,
                "matrix": ga_result.best_solution,
            },
            "bee": {
                "best_fitness": bee_result.best_fitness,
                "best_objective": bee_result.best_objective,
                "feasible": bee_result.feasible,
                "time_s": bee_result.elapsed_s,
                "overlaps_count": bee_result.overlaps_count,
                "matrix": bee_result.best_solution,
            },
        })

    save_results_csv(results_dir / "example_results.csv", rows)
    save_history(results_dir / "example_results_history.json", str(graph_path.name), args.repetitions, args.iterations, history_runs)
    save_matrices(results_dir / "example_results_matrices.json", str(graph_path.name), args.repetitions, args.iterations, {
        "edges_count": instance.edges_count,
        "crews_count": instance.crews_count,
        "budget": float(instance.budget),
        "edge_ids": [f"e{i + 1}" for i in range(instance.edges_count)],
        "base_times": [int(t) for t in instance.base_times],
        "loads": [float(l) for l in instance.loads],
        "crew_costs": [float(c) for c in instance.crew_costs],
    },
    {
        "GA": matrix_runs[-1]["ga"],
        "Bee": matrix_runs[-1]["bee"],
    },
    matrix_runs)

    render_graph(results_dir / "example_results_matrices.json", results_dir / "example_graph_assignments.png")
    print("Gotowe. Sprawdź pliki w katalogu results/")


if __name__ == "__main__":
    main()
