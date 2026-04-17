from __future__ import annotations

import random
from typing import List

from src.model import ProblemInstance


def generate_instance(
    edges_count: int,
    crews_count: int,
    seed: int,
    base_time_range: tuple[int, int] = (3, 24),
    load_range: tuple[int, int] = (1, 12),
    crew_cost_range: tuple[int, int] = (4, 16),
    budget_ratio: float = 0.65,
) -> ProblemInstance:
    """Create synthetic instance with reproducible randomness."""
    rng = random.Random(seed)

    base_times: List[int] = [rng.randint(*base_time_range) for _ in range(edges_count)]
    loads: List[float] = [float(rng.randint(*load_range)) for _ in range(edges_count)]
    crew_costs: List[float] = [float(rng.randint(*crew_cost_range)) for _ in range(crews_count)]

    max_cost = sum(crew_costs)
    budget = max(1.0, round(max_cost * budget_ratio, 2))

    return ProblemInstance(
        base_times=base_times,
        loads=loads,
        crew_costs=crew_costs,
        budget=budget,
    )
