"""Finite-speed obstruction to strict fixed-period binary branching."""


def capacity_at_generation(
    width: int,
    height: int,
    population: int,
    period: int,
    generation: int,
) -> tuple[int, int]:
    """Return required live cells and available causal-cone cells."""
    if min(width, height, population, period, generation) <= 0:
        raise ValueError("all arguments must be positive")
    required = population * (1 << generation)
    available = (
        (width + 2 * period * generation)
        * (height + 2 * period * generation)
    )
    return required, available


def first_capacity_contradiction(
    width: int,
    height: int,
    population: int,
    period: int,
) -> int:
    """Find n where 2**n disjoint copies cannot fit in the Life light cone."""
    generation = 1
    while True:
        required, available = capacity_at_generation(
            width, height, population, period, generation
        )
        if required > available:
            return generation
        generation += 1
