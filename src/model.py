from __future__ import annotations

from dataclasses import dataclass, field
from math import ceil
from typing import Any, Dict, List, Sequence, Tuple


Matrix = List[List[int]]


@dataclass(frozen=True)
class ProblemInstance:
    base_times: List[int]  # t_s for each road edge
    loads: List[float]  # d for each road edge
    crew_costs: List[float]  # k_i for each crew
    budget: float  # b
    edge_ids: List[str] = field(default_factory=list)

    @property
    def edges_count(self) -> int:
        return len(self.base_times)

    @property
    def crews_count(self) -> int:
        return len(self.crew_costs)


@dataclass
class ScheduleInfo:
    edge_starts: List[float]
    edge_ends: List[float]
    edge_durations: List[int]
    crew_intervals: List[List[Tuple[float, float, int]]]
    overlaps: List[Dict[str, Any]]


@dataclass
class EvaluationResult:
    fitness: float
    objective: float
    feasible: bool
    penalty_total: float
    budget_excess: float
    overlaps_count: int
    schedule: ScheduleInfo


def _repair_assignment(solution: Matrix) -> None:
    """Ensure each edge has at least one assigned crew."""
    if not solution:
        return
    crews = len(solution)
    edges = len(solution[0])
    for edge in range(edges):
        assigned = sum(solution[crew][edge] for crew in range(crews))
        if assigned == 0:
            solution[edge % crews][edge] = 1


def _repair_budget(instance: ProblemInstance, solution: Matrix) -> None:
    """Reduce active crews until total cost is within budget when possible."""
    crews = instance.crews_count
    edges = instance.edges_count

    if crews == 0 or edges == 0:
        return

    # Prefer keeping cheaper crews active.
    crews_by_cost = sorted(range(crews), key=lambda idx: instance.crew_costs[idx])
    active = {i for i in range(crews) if any(solution[i][e] for e in range(edges))}

    def total_cost(active_set: set[int]) -> float:
        return sum(instance.crew_costs[i] for i in active_set)

    if total_cost(active) <= instance.budget:
        return

    # Keep at least one active crew for coverage.
    for expensive in sorted(active, key=lambda idx: instance.crew_costs[idx], reverse=True):
        if len(active) <= 1:
            break

        # Find replacement crew among currently active cheaper crews.
        replacement_candidates = [c for c in crews_by_cost if c in active and c != expensive]
        if not replacement_candidates:
            continue
        replacement = replacement_candidates[0]

        # Move assignments from expensive crew to replacement.
        for edge in range(edges):
            if solution[expensive][edge] == 1:
                solution[replacement][edge] = 1
                solution[expensive][edge] = 0

        active.discard(expensive)
        if total_cost(active) <= instance.budget:
            return


def clone_solution(solution: Matrix) -> Matrix:
    return [row[:] for row in solution]


def flatten(solution: Matrix) -> List[int]:
    return [value for row in solution for value in row]


def unflatten(flat: Sequence[int], crews_count: int, edges_count: int) -> Matrix:
    matrix: Matrix = []
    idx = 0
    for _ in range(crews_count):
        row = [int(flat[idx + col]) for col in range(edges_count)]
        matrix.append(row)
        idx += edges_count
    return matrix


def _edge_durations_with_unassigned_penalty(
    instance: ProblemInstance,
    solution: Matrix,
    penalty_unassigned: float,
) -> Tuple[List[int], float]:
    crews = instance.crews_count
    edges = instance.edges_count
    durations: List[int] = []
    penalty = 0.0

    for edge in range(edges):
        assigned_crews = sum(solution[crew][edge] for crew in range(crews))
        if assigned_crews <= 0:
            penalty += penalty_unassigned
            assigned_crews = 1
        road_time = ceil((2 ** (-assigned_crews + 1)) * instance.base_times[edge])
        durations.append(road_time)

    return durations, penalty


def _build_schedule(instance: ProblemInstance, solution: Matrix, edge_durations: List[int]) -> ScheduleInfo:
    edges = instance.edges_count
    crews = instance.crews_count

    edge_starts = [0.0 for _ in range(edges)]
    edge_ends = [0.0 for _ in range(edges)]
    crew_intervals: List[List[Tuple[float, float, int]]] = [[] for _ in range(crews)]
    crew_available = [0.0 for _ in range(crews)]

    # Higher load*time roads are scheduled first.
    edge_order = sorted(range(edges), key=lambda e: instance.loads[e] * instance.base_times[e], reverse=True)

    for edge in edge_order:
        assigned = [crew for crew in range(crews) if solution[crew][edge] == 1]
        if not assigned:
            continue

        crew_ready = max(crew_available[crew] for crew in assigned)
        start = crew_ready
        end = start + float(edge_durations[edge])

        edge_starts[edge] = start
        edge_ends[edge] = end

        for crew in assigned:
            crew_intervals[crew].append((start, end, edge))
            crew_available[crew] = end

    overlaps: List[Dict[str, Any]] = []
    for crew, intervals in enumerate(crew_intervals):
        intervals.sort(key=lambda item: (item[0], item[1]))
        for idx in range(1, len(intervals)):
            prev_start, prev_end, prev_edge = intervals[idx - 1]
            cur_start, cur_end, cur_edge = intervals[idx]
            if cur_start < prev_end:
                overlaps.append(
                    {
                        "crew": crew,
                        "edge_a": prev_edge,
                        "edge_b": cur_edge,
                        "interval_a": [prev_start, prev_end],
                        "interval_b": [cur_start, cur_end],
                    }
                )

    return ScheduleInfo(
        edge_starts=edge_starts,
        edge_ends=edge_ends,
        edge_durations=edge_durations,
        crew_intervals=crew_intervals,
        overlaps=overlaps,
    )


def evaluate_solution_details(
    instance: ProblemInstance,
    solution: Matrix,
    penalty_budget: float = 1000.0,
    penalty_unassigned: float = 10000.0,
    penalty_overlap_hard: float = 1_000_000_000.0,
) -> EvaluationResult:
    """
    Evaluate solution with explicit schedule and hard overlap penalty.
    Lower fitness is better.
    """
    crews = instance.crews_count
    edges = instance.edges_count

    if len(solution) != crews or any(len(row) != edges for row in solution):
        raise ValueError("Solution dimensions do not match instance dimensions")

    edge_durations, penalty = _edge_durations_with_unassigned_penalty(instance, solution, penalty_unassigned)
    raw_objective = sum(instance.loads[edge] * edge_durations[edge] for edge in range(edges))

    used_crews = [1 if any(solution[crew][edge] for edge in range(edges)) else 0 for crew in range(crews)]
    total_cost = sum(used_crews[crew] * instance.crew_costs[crew] for crew in range(crews))
    budget_excess = max(0.0, total_cost - instance.budget)
    if budget_excess > 0:
        penalty += penalty_budget * budget_excess

    schedule = _build_schedule(instance, solution, edge_durations)
    overlaps_count = len(schedule.overlaps)
    if overlaps_count > 0:
        penalty += penalty_overlap_hard * overlaps_count

    feasible = penalty == 0.0 and overlaps_count == 0
    return EvaluationResult(
        fitness=raw_objective + penalty,
        objective=raw_objective,
        feasible=feasible,
        penalty_total=penalty,
        budget_excess=budget_excess,
        overlaps_count=overlaps_count,
        schedule=schedule,
    )


def evaluate_solution(
    instance: ProblemInstance,
    solution: Matrix,
    penalty_budget: float = 1000.0,
    penalty_unassigned: float = 10000.0,
) -> Tuple[float, float, bool]:
    """
    Returns tuple: (fitness_with_penalties, raw_objective, is_feasible).
    Lower is better.
    """
    details = evaluate_solution_details(
        instance=instance,
        solution=solution,
        penalty_budget=penalty_budget,
        penalty_unassigned=penalty_unassigned,
    )
    return details.fitness, details.objective, details.feasible


def repair_solution(solution: Matrix, instance: ProblemInstance | None = None) -> Matrix:
    repaired = clone_solution(solution)
    _repair_assignment(repaired)
    if instance is not None:
        _repair_budget(instance, repaired)
        _repair_assignment(repaired)
    return repaired
