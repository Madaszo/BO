from __future__ import annotations

import random
from dataclasses import dataclass
from time import perf_counter
from typing import List

from src.model import Matrix, ProblemInstance, ScheduleInfo, evaluate_solution_details, repair_solution


@dataclass
class BeeConfig:
    colony_size: int = 60
    iterations: int = 180
    limit: int = 30
    neighborhood_flips: int = 2
    seed: int = 7


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


def _neighbor(solution: Matrix, flips: int, instance: ProblemInstance, rng: random.Random) -> Matrix:
    neigh = [row[:] for row in solution]
    crews = len(neigh)
    edges = len(neigh[0]) if crews else 0
    total = crews * edges

    for _ in range(max(1, flips)):
        pos = rng.randrange(total)
        i = pos // edges
        j = pos % edges
        neigh[i][j] = 1 - neigh[i][j]

    return repair_solution(neigh, instance)


def _roulette(scores: List[float], rng: random.Random) -> int:
    # Lower fitness is better, convert to positive attractiveness.
    attractiveness = [1.0 / (1.0 + s) for s in scores]
    total = sum(attractiveness)
    pick = rng.random() * total
    run = 0.0
    for idx, val in enumerate(attractiveness):
        run += val
        if run >= pick:
            return idx
    return len(scores) - 1


def solve_bee(instance: ProblemInstance, cfg: BeeConfig) -> SolverResult:
    rng = random.Random(cfg.seed)
    start = perf_counter()

    food_count = max(2, cfg.colony_size // 2)
    foods: List[Matrix] = [_random_solution(instance, rng) for _ in range(food_count)]
    trials = [0 for _ in range(food_count)]

    fits = []
    objs = []
    feas = []
    schedules: List[ScheduleInfo] = []
    overlaps: List[int] = []
    for food in foods:
        details = evaluate_solution_details(instance, food)
        fits.append(details.fitness)
        objs.append(details.objective)
        feas.append(details.feasible)
        schedules.append(details.schedule)
        overlaps.append(details.overlaps_count)

    best_idx = min(range(food_count), key=lambda i: fits[i])
    best_fit = fits[best_idx]
    best_obj = objs[best_idx]
    best_feasible = feas[best_idx]
    best_solution = [row[:] for row in foods[best_idx]]
    best_schedule = schedules[best_idx]
    best_overlaps = overlaps[best_idx]

    history: List[float] = []

    for _ in range(cfg.iterations):
        # Employed bees phase.
        for i in range(food_count):
            candidate = _neighbor(foods[i], cfg.neighborhood_flips, instance, rng)
            c_details = evaluate_solution_details(instance, candidate)
            c_fit, c_obj, c_feasible = c_details.fitness, c_details.objective, c_details.feasible
            if c_fit < fits[i]:
                foods[i] = candidate
                fits[i] = c_fit
                objs[i] = c_obj
                feas[i] = c_feasible
                schedules[i] = c_details.schedule
                overlaps[i] = c_details.overlaps_count
                trials[i] = 0
            else:
                trials[i] += 1

        # Onlooker bees phase.
        for _ in range(food_count):
            i = _roulette(fits, rng)
            candidate = _neighbor(foods[i], cfg.neighborhood_flips, instance, rng)
            c_details = evaluate_solution_details(instance, candidate)
            c_fit, c_obj, c_feasible = c_details.fitness, c_details.objective, c_details.feasible
            if c_fit < fits[i]:
                foods[i] = candidate
                fits[i] = c_fit
                objs[i] = c_obj
                feas[i] = c_feasible
                schedules[i] = c_details.schedule
                overlaps[i] = c_details.overlaps_count
                trials[i] = 0
            else:
                trials[i] += 1

        # Scout phase.
        for i in range(food_count):
            if trials[i] > cfg.limit:
                foods[i] = _random_solution(instance, rng)
                details = evaluate_solution_details(instance, foods[i])
                fits[i], objs[i], feas[i] = details.fitness, details.objective, details.feasible
                schedules[i] = details.schedule
                overlaps[i] = details.overlaps_count
                trials[i] = 0

        cur_best = min(range(food_count), key=lambda i: fits[i])
        history.append(fits[cur_best])
        if fits[cur_best] < best_fit:
            best_fit = fits[cur_best]
            best_obj = objs[cur_best]
            best_feasible = feas[cur_best]
            best_solution = [row[:] for row in foods[cur_best]]
            best_schedule = schedules[cur_best]
            best_overlaps = overlaps[cur_best]

    elapsed = perf_counter() - start

    return SolverResult(
        name="Bee",
        best_fitness=best_fit,
        best_objective=best_obj,
        feasible=best_feasible,
        elapsed_s=elapsed,
        history=history,
        best_solution=best_solution,
        best_schedule=best_schedule,
        overlaps_count=best_overlaps,
    )
