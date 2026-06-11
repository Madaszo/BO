#!/usr/bin/env python3
"""Single entry point for the full workflow.

Stages:
1. Import road data from `road_data.json` into `parsing_results.json`.
2. Run experiments with `run_experiments.py`.
3. Render visualizations with `visualize_graph.py`.
"""

from __future__ import annotations

import argparse
import json
import math
import subprocess
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parent
DEFAULT_ROAD_DATA = REPO_ROOT / "road_data.json"
DEFAULT_PARSING_OUTPUT = REPO_ROOT / "parsing_results.json"
DEFAULT_RESULTS_DIR = REPO_ROOT / "results"
DEFAULT_CREW_COSTS = [6, 8, 7, 10, 9, 11]
DEFAULT_BUDGET = 400.0

ROAD_WEIGHTS = {
    "unclassified": 1,
    "living_street": 2,
    "residential": 2,
    "tertiary": 4,
    "secondary": 8,
    "primary": 16,
    "trunk": 32,
    "motorway": 64,
    "tertiary_link": 3,
    "secondary_link": 6,
    "primary_link": 12,
    "trunk_link": 25,
    "motorway_link": 51,
}


def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    d_lat = (lat2 - lat1) * math.pi / 180.0
    d_lon = (lon2 - lon1) * math.pi / 180.0
    lat1 = lat1 * math.pi / 180.0
    lat2 = lat2 * math.pi / 180.0
    a = math.sin(d_lat / 2) ** 2 + math.sin(d_lon / 2) ** 2 * math.cos(lat1) * math.cos(lat2)
    return 6371.0 * 2.0 * math.asin(math.sqrt(a))


def build_parsing_results(road_data_path: Path) -> dict[str, Any]:
    data = json.loads(road_data_path.read_text(encoding="utf-8"))

    graph: dict[str, Any] = {
        "edges": [],
        "nodes": [],
        "crew_costs": DEFAULT_CREW_COSTS,
        "budget": DEFAULT_BUDGET,
    }

    for road in data.get("elements", []):
        road_id = str(road.get("id", f"way_{len(graph['edges'])}"))
        nodes = road.get("nodes", [])
        geometry = road.get("geometry", [])
        tags = road.get("tags", {})

        for node_id, geom in zip(nodes, geometry):
            graph["nodes"].append({"id": node_id, "position": geom})

        for idx in range(max(0, len(nodes) - 1)):
            start_node = nodes[idx]
            end_node = nodes[idx + 1]
            start_lat = geometry[idx]["lat"]
            start_lon = geometry[idx]["lon"]
            end_lat = geometry[idx + 1]["lat"]
            end_lon = geometry[idx + 1]["lon"]
            distance = haversine(start_lat, start_lon, end_lat, end_lon)
            lanes = int(tags["lanes"]) if "lanes" in tags else 2
            highway_type = tags.get("highway")
            graph["edges"].append(
                {
                    "id": f"{road_id}-{idx}",
                    "base_time": math.ceil(distance * lanes * 1000),
                    "load": ROAD_WEIGHTS.get(highway_type, 1),
                    "start": start_node,
                    "end": end_node,
                }
            )

    return graph


def import_road_data(road_data_path: Path, parsing_output_path: Path) -> None:
    if not road_data_path.exists():
        raise FileNotFoundError(f"Road data file not found: {road_data_path}")

    graph = build_parsing_results(road_data_path)
    parsing_output_path.write_text(json.dumps(graph, indent=2), encoding="utf-8")
    print(f"[import] saved {parsing_output_path}")


def run_command(command: list[str], cwd: Path) -> None:
    print("[run]", " ".join(command))
    subprocess.run(command, cwd=cwd, check=True)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run import -> experiments -> visualization in one step")
    parser.add_argument("--road-data", type=Path, default=DEFAULT_ROAD_DATA, help="Input OSM export JSON")
    parser.add_argument("--parsing-output", type=Path, default=DEFAULT_PARSING_OUTPUT, help="Generated graph JSON used by experiments")
    parser.add_argument("--graph", type=Path, default=None, help="Graph JSON used by experiments; defaults to parsing output")
    parser.add_argument("--out", type=str, default="benchmark_results.csv", help="CSV filename in results/")
    parser.add_argument("--repetitions", type=int, default=10, help="Number of repetitions for a single run")
    parser.add_argument("--iterations", type=int, default=120, help="Generations/iterations for a single run")
    parser.add_argument("--ga-config", type=str, default="", help="Optional GA config JSON file")
    parser.add_argument("--bee-config", type=str, default="", help="Optional Bee config JSON file")
    parser.add_argument("--runs-config", type=Path, default=None, help="Optional JSON file with multiple run definitions")
    parser.add_argument("--skip-import", action="store_true", help="Skip road data import stage")
    parser.add_argument("--skip-experiments", action="store_true", help="Skip experiment stage")
    parser.add_argument("--skip-visualize", action="store_true", help="Skip visualization stage")
    return parser.parse_args()


def main() -> None:
    args = _parse_args()

    if not args.skip_import:
        import_road_data(args.road_data, args.parsing_output)

    graph_for_experiments = args.graph or args.parsing_output
    experiments_script = REPO_ROOT / "run_experiments.py"

    if not args.skip_experiments:
        command = [
            sys.executable,
            str(experiments_script),
            "--graph",
            str(graph_for_experiments),
        ]

        if args.runs_config is not None:
            command.extend(["--runs-config", str(args.runs_config)])
            command.extend(["--out", args.out])
        else:
            command.extend(["--repetitions", str(args.repetitions)])
            command.extend(["--iterations", str(args.iterations)])
            command.extend(["--out", args.out])
            if args.ga_config:
                command.extend(["--ga-config", args.ga_config])
            if args.bee_config:
                command.extend(["--bee-config", args.bee_config])

        run_command(command, REPO_ROOT)

    if not args.skip_visualize:
        run_command([sys.executable, str(REPO_ROOT / "visualize_graph.py")], REPO_ROOT)


if __name__ == "__main__":
    main()