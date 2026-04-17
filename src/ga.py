from __future__ import annotations

import random
from dataclasses import dataclass
from time import perf_counter
from typing import List

from src.model import (
    ScheduleInfo,
    Matrix,
    ProblemInstance,
    evaluate_solution_details,
    flatten,
    repair_solution,
    unflatten,
)


@dataclass
class GAConfig:
    population_size: int = 80
    generations: int = 180
    crossover_rate: float = 0.85
    mutation_rate: float = 0.03
    tournament_size: int = 3
    elite_count: int = 2
    seed: int = 42


@dataclass
class SolverResult:
    name: str
    best_fitness: float
    best_objective: float
    feasible: bool
    elapsed_s: float
    history: List[float]
    best_solution: Matrix
    best_schedule: ScheduleInfo
    overlaps_count: int


def _random_solution(instance: ProblemInstance, rng: random.Random) -> Matrix:
    solution: Matrix = []
    for _ in range(instance.crews_count):
        row = [1 if rng.random() < 0.35 else 0 for _ in range(instance.edges_count)]
        solution.append(row)
    return repair_solution(solution, instance)


def _tournament_selection(scored: List[tuple[float, Matrix]], rng: random.Random, k: int) -> Matrix:
    picks = rng.sample(scored, k=min(k, len(scored)))
    picks.sort(key=lambda x: x[0])
    return picks[0][1]


def _crossover(parent_a: Matrix, parent_b: Matrix, instance: ProblemInstance, rng: random.Random) -> tuple[Matrix, Matrix]:
    a_flat = flatten(parent_a)
    b_flat = flatten(parent_b)
    if len(a_flat) != len(b_flat):
        raise ValueError("Parent representations must have equal length")

    if len(a_flat) < 2:
        return parent_a, parent_b

    point = rng.randint(1, len(a_flat) - 1)
    child_1 = a_flat[:point] + b_flat[point:]
    child_2 = b_flat[:point] + a_flat[point:]

    c1 = unflatten(child_1, instance.crews_count, instance.edges_count)
    c2 = unflatten(child_2, instance.crews_count, instance.edges_count)
    return repair_solution(c1, instance), repair_solution(c2, instance)


def _mutate(solution: Matrix, mutation_rate: float, instance: ProblemInstance, rng: random.Random) -> Matrix:
    mutated: Matrix = [row[:] for row in solution]
    for i in range(len(mutated)):
        for j in range(len(mutated[i])):
            if rng.random() < mutation_rate:
                mutated[i][j] = 1 - mutated[i][j]
    return repair_solution(mutated, instance)


def solve_ga(instance: ProblemInstance, cfg: GAConfig) -> SolverResult:
    rng = random.Random(cfg.seed)
    start = perf_counter()

    population: List[Matrix] = [_random_solution(instance, rng) for _ in range(cfg.population_size)]
    history: List[float] = []

    best_fit = float("inf")
    best_obj = float("inf")
    best_sol: Matrix | None = None
    best_feasible = False
    best_schedule: ScheduleInfo | None = None
    best_overlaps = 0

    for _ in range(cfg.generations):
        scored: List[tuple[float, Matrix]] = []
        for sol in population:
            details = evaluate_solution_details(instance, sol)
            fit, obj, feasible = details.fitness, details.objective, details.feasible
            scored.append((fit, sol))
            if fit < best_fit:
                best_fit = fit
                best_obj = obj
                best_sol = [row[:] for row in sol]
                best_feasible = feasible
                best_schedule = details.schedule
                best_overlaps = details.overlaps_count

        scored.sort(key=lambda x: x[0])
        history.append(scored[0][0])

        next_population: List[Matrix] = [scored[i][1] for i in range(min(cfg.elite_count, len(scored)))]

        while len(next_population) < cfg.population_size:
            p1 = _tournament_selection(scored, rng, cfg.tournament_size)
            p2 = _tournament_selection(scored, rng, cfg.tournament_size)

            if rng.random() < cfg.crossover_rate:
                c1, c2 = _crossover(p1, p2, instance, rng)
            else:
                c1, c2 = [row[:] for row in p1], [row[:] for row in p2]

            c1 = _mutate(c1, cfg.mutation_rate, instance, rng)
            c2 = _mutate(c2, cfg.mutation_rate, instance, rng)

            next_population.append(c1)
            if len(next_population) < cfg.population_size:
                next_population.append(c2)

        population = next_population

    elapsed = perf_counter() - start
    if best_sol is None or best_schedule is None:
        raise RuntimeError("GA failed to produce a solution")

    return SolverResult(
        name="GA",
        best_fitness=best_fit,
        best_objective=best_obj,
        feasible=best_feasible,
        elapsed_s=elapsed,
        history=history,
        best_solution=[row[:] for row in best_sol],
        best_schedule=best_schedule,
        overlaps_count=best_overlaps,
    )
