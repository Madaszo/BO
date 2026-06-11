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
    history_runs = []

    for rep in range(repetitions):
        print(f"Running repetition {rep + 1}/{repetitions} for fixed graph...")

        # Create GA and Bee configs with defaults; can be overridden by
        # per-run JSON configuration files passed via command-line args.
        ga_kwargs = {
            "population_size": 80,
            "generations": iterations,
            "crossover_rate": 0.85,
            "mutation_rate": 0.03,
            "tournament_size": 3,
            "elite_count": 2,
            "seed": 2000 + rep,
        }

        bee_kwargs = {
            "colony_size": 60,
            "iterations": iterations,
            "limit": 30,
            "neighborhood_flips": 2,
            "seed": 3000 + rep,
        }

        # If config files or inline dicts were provided through args or runs-config,
        # load and merge them. We accept either a path (str) or an already-loaded
        # dict on the run_single_graph attributes.
        if hasattr(run_single_graph, "ga_config_json") and run_single_graph.ga_config_json:
            try:
                if isinstance(run_single_graph.ga_config_json, dict):
                    gj = run_single_graph.ga_config_json
                else:
                    gj = json.loads(Path(run_single_graph.ga_config_json).read_text(encoding="utf-8"))
                for k in list(gj.keys()):
                    if k in ga_kwargs:
                        ga_kwargs[k] = gj[k]
            except Exception:
                print(f"Warning: could not read GA config {run_single_graph.ga_config_json}")

        if hasattr(run_single_graph, "bee_config_json") and run_single_graph.bee_config_json:
            try:
                if isinstance(run_single_graph.bee_config_json, dict):
                    bj = run_single_graph.bee_config_json
                else:
                    bj = json.loads(Path(run_single_graph.bee_config_json).read_text(encoding="utf-8"))
                for k in list(bj.keys()):
                    if k in bee_kwargs:
                        bee_kwargs[k] = bj[k]
            except Exception:
                print(f"Warning: could not read Bee config {run_single_graph.bee_config_json}")

        ga_result = solve_ga(instance, GAConfig(**ga_kwargs))
        bee_result = solve_bee(instance, BeeConfig(**bee_kwargs))

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

        history_runs.append(
            {
                "rep": rep,
                "ga": {
                    "history_best_fitness": ga_result.history,
                    "history_length": len(ga_result.history),
                },
                "bee": {
                    "history_best_fitness": bee_result.history,
                    "history_length": len(bee_result.history),
                },
            }
        )

    out_csv = Path("results") / out_file
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    out_matrices = out_csv.with_name(out_csv.stem + "_matrices.json")
    out_history = out_csv.with_name(out_csv.stem + "_history.json")

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

    history_payload = {
        "graph_file": graph_file,
        "repetitions": repetitions,
        "iterations": iterations,
        "notes": {
            "ga": "history_best_fitness contains best fitness value from each generation",
            "bee": "history_best_fitness contains best fitness value from each iteration",
        },
        "runs": history_runs,
    }
    out_history.write_text(json.dumps(history_payload, indent=2), encoding="utf-8")

    print(f"Saved raw results to: {out_csv}")
    print(f"Saved solution matrices to: {out_matrices}")
    print(f"Saved optimization histories to: {out_history}")

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
    parser.add_argument("--ga-config", type=str, default="", help="Optional JSON config file for GA parameters (path)")
    parser.add_argument("--bee-config", type=str, default="", help="Optional JSON config file for Bee parameters (path)")
    parser.add_argument("--runs-config", type=str, default="", help="Optional JSON file with array of run definitions; each run can override graph/repetitions/iterations/ga_config/bee_config/out")
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    # If a runs-config is provided, execute each run sequentially. Each run entry
    # may contain: graph, repetitions, iterations, out, ga_config, bee_config.
    if args.runs_config:
        try:
            runs = json.loads(Path(args.runs_config).read_text(encoding="utf-8"))
        except Exception as e:
            print(f"Could not read runs config {args.runs_config}: {e}")
            raise

        if isinstance(runs, dict):
            runs = [runs]

        for idx, rdef in enumerate(runs):
            graph_file = rdef.get("graph", args.graph)
            repetitions = int(rdef.get("repetitions", args.repetitions))
            iterations = int(rdef.get("iterations", args.iterations))
            # Build output filename: prefer explicit 'out' in run definition, otherwise
            # append a run index to the CLI-provided out filename.
            if "out" in rdef:
                out_file = rdef.get("out")
            else:
                base = args.out
                if base.endswith(".csv"):
                    out_file = base[:-4] + f"_run{idx+1}.csv"
                else:
                    out_file = base + f"_run{idx+1}.csv"

            # Attach GA/Bee configs: can be dict or path string
            run_single_graph.ga_config_json = rdef.get("ga_config") or args.ga_config
            run_single_graph.bee_config_json = rdef.get("bee_config") or args.bee_config

            print(f"\n=== Running config {idx+1}/{len(runs)}: graph={graph_file}, reps={repetitions}, iters={iterations} ===")
            run_single_graph(graph_file=graph_file, repetitions=repetitions, iterations=iterations, out_file=out_file)

        # Clean up attributes
        run_single_graph.ga_config_json = None
        run_single_graph.bee_config_json = None
    else:
        # Attach optional config file paths to the run function so they are available
        # when creating solver configs.
        run_single_graph.ga_config_json = args.ga_config
        run_single_graph.bee_config_json = args.bee_config

        run_single_graph(graph_file=args.graph, repetitions=args.repetitions, iterations=args.iterations, out_file=args.out)
