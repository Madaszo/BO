from __future__ import annotations

import argparse
import csv
import json
import statistics
from pathlib import Path

from src.bee import BeeConfig, solve_bee
from src.ga import GAConfig, solve_ga
from src.model import ProblemInstance


def _load_instance_from_json(path: Path) -> ProblemInstance:
    raw = json.loads(path.read_text(encoding="utf-8"))

    if "edges" not in raw or "crew_costs" not in raw or "budget" not in raw:
        raise ValueError("Input JSON must contain keys: edges, crew_costs, budget")

    edges = raw["edges"]
    edge_ids = [str(edge.get("id", f"e{idx}")) for idx, edge in enumerate(edges)]
    base_times = [int(edge["base_time"]) for edge in edges]
    loads = [float(edge["load"]) for edge in edges]
    crew_costs = [float(c) for c in raw["crew_costs"]]
    budget = float(raw["budget"])

    return ProblemInstance(
        base_times=base_times,
        loads=loads,
        crew_costs=crew_costs,
        budget=budget,
        edge_ids=edge_ids,
    )


def run_single_graph(graph_file: str, repetitions: int, iterations: int, out_file: str) -> None:
    instance = _load_instance_from_json(Path(graph_file))

    rows = []
    matrix_runs = []

    for rep in range(repetitions):
        print(f"Running repetition {rep + 1}/{repetitions} for fixed graph...")

        ga_result = solve_ga(
            instance,
            GAConfig(
                population_size=80,
                generations=iterations,
                crossover_rate=0.85,
                mutation_rate=0.03,
                seed=2000 + rep,
            ),
        )

        bee_result = solve_bee(
            instance,
            BeeConfig(
                colony_size=60,
                iterations=iterations,
                limit=30,
                neighborhood_flips=2,
                seed=3000 + rep,
            ),
        )

        rows.append(
            {
                "rep": rep,
                "solver": ga_result.name,
                "best_fitness": round(ga_result.best_fitness, 4),
                "best_objective": round(ga_result.best_objective, 4),
                "feasible": int(ga_result.feasible),
                "time_s": round(ga_result.elapsed_s, 4),
            }
        )
        rows.append(
            {
                "rep": rep,
                "solver": bee_result.name,
                "best_fitness": round(bee_result.best_fitness, 4),
                "best_objective": round(bee_result.best_objective, 4),
                "feasible": int(bee_result.feasible),
                "time_s": round(bee_result.elapsed_s, 4),
            }
        )

        matrix_runs.append(
            {
                "rep": rep,
                "ga": {
                    "best_fitness": ga_result.best_fitness,
                    "best_objective": ga_result.best_objective,
                    "feasible": ga_result.feasible,
                    "time_s": ga_result.elapsed_s,
                    "overlaps_count": ga_result.overlaps_count,
                    "matrix": ga_result.best_solution,
                    "schedule": {
                        "edge_starts": ga_result.best_schedule.edge_starts,
                        "edge_ends": ga_result.best_schedule.edge_ends,
                        "edge_durations": ga_result.best_schedule.edge_durations,
                        "crew_intervals": ga_result.best_schedule.crew_intervals,
                        "overlaps": ga_result.best_schedule.overlaps,
                    },
                },
                "bee": {
                    "best_fitness": bee_result.best_fitness,
                    "best_objective": bee_result.best_objective,
                    "feasible": bee_result.feasible,
                    "time_s": bee_result.elapsed_s,
                    "overlaps_count": bee_result.overlaps_count,
                    "matrix": bee_result.best_solution,
                    "schedule": {
                        "edge_starts": bee_result.best_schedule.edge_starts,
                        "edge_ends": bee_result.best_schedule.edge_ends,
                        "edge_durations": bee_result.best_schedule.edge_durations,
                        "crew_intervals": bee_result.best_schedule.crew_intervals,
                        "overlaps": bee_result.best_schedule.overlaps,
                    },
                },
            }
        )

    out_dir = Path("results")
    out_dir.mkdir(exist_ok=True)
    out_csv = out_dir / out_file
    out_matrices = out_dir / out_file.replace(".csv", "_matrices.json")

    with out_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["rep", "solver", "best_fitness", "best_objective", "feasible", "time_s"],
        )
        writer.writeheader()
        writer.writerows(rows)

    best_ga = min((r for r in matrix_runs), key=lambda x: x["ga"]["best_fitness"])
    best_bee = min((r for r in matrix_runs), key=lambda x: x["bee"]["best_fitness"])

    matrices_payload = {
        "graph_file": graph_file,
        "repetitions": repetitions,
        "iterations": iterations,
        "instance": {
            "edges_count": instance.edges_count,
            "crews_count": instance.crews_count,
            "budget": instance.budget,
            "edge_ids": instance.edge_ids,
            "base_times": instance.base_times,
            "loads": instance.loads,
            "crew_costs": instance.crew_costs,
        },
        "best_overall": {
            "ga": best_ga["ga"],
            "bee": best_bee["bee"],
        },
        "runs": matrix_runs,
    }
    out_matrices.write_text(json.dumps(matrices_payload, indent=2), encoding="utf-8")

    print(f"Saved raw results to: {out_csv}")
    print(f"Saved solution matrices to: {out_matrices}")

    print("\nSummary for fixed graph:")
    for solver in ("GA", "Bee"):
        subset = [r for r in rows if r["solver"] == solver]
        fitnesses = [float(r["best_fitness"]) for r in subset]
        objectives = [float(r["best_objective"]) for r in subset]
        feas_ratio = sum(int(r["feasible"]) for r in subset) / len(subset)
        times = [float(r["time_s"]) for r in subset]

        print(
            f"- {solver:>3} | "
            f"fit mean={statistics.mean(fitnesses):8.2f}, "
            f"fit std={statistics.pstdev(fitnesses):7.2f}, "
            f"obj mean={statistics.mean(objectives):8.2f}, "
            f"feasible={feas_ratio:5.1%}, "
            f"time mean={statistics.mean(times):6.3f}s"
        )


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compare GA and Bee algorithm on one fixed road graph")
    parser.add_argument("--graph", type=str, required=True, help="Path to input graph JSON file")
    parser.add_argument("--repetitions", type=int, default=10, help="Number of runs for the fixed graph")
    parser.add_argument("--iterations", type=int, default=120, help="Generations/iterations per solver")
    parser.add_argument("--out", type=str, default="benchmark_results.csv", help="Output CSV filename in results/")
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    run_single_graph(graph_file=args.graph, repetitions=args.repetitions, iterations=args.iterations, out_file=args.out)
