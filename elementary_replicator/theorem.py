"""Finite-speed obstructions to fixed-period branching."""

from collections.abc import Sequence


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


def phase_counts(
    substitution: Sequence[Sequence[int]],
    initial_phase: int,
    generation: int,
) -> tuple[int, ...]:
    """Return exact multitype-substitution counts after ``generation`` steps."""
    size = len(substitution)
    if size == 0 or any(len(row) != size for row in substitution):
        raise ValueError("substitution must be a nonempty square matrix")
    if any(value < 0 for row in substitution for value in row):
        raise ValueError("substitution entries must be nonnegative")
    if not 0 <= initial_phase < size:
        raise ValueError("initial phase is outside the matrix")
    if generation < 0:
        raise ValueError("generation must be nonnegative")

    counts = [0] * size
    counts[initial_phase] = 1
    for _ in range(generation):
        counts = [
            sum(
                counts[source] * substitution[source][target]
                for source in range(size)
            )
            for target in range(size)
        ]
    return tuple(counts)


def phased_capacity_at_generation(
    substitution: Sequence[Sequence[int]],
    initial_phase: int,
    minimum_phase_population: int,
    width: int,
    height: int,
    period: int,
    generation: int,
    radius: int = 1,
) -> tuple[tuple[int, ...], int, int]:
    """Return phase counts, required cells, and causal-cone capacity."""
    if min(minimum_phase_population, width, height, period) <= 0 or radius < 0:
        raise ValueError("sizes must be positive and radius nonnegative")
    counts = phase_counts(substitution, initial_phase, generation)
    required = minimum_phase_population * sum(counts)
    reach = radius * period * generation
    available = (width + 2 * reach) * (height + 2 * reach)
    return counts, required, available


def first_phased_capacity_contradiction(
    substitution: Sequence[Sequence[int]],
    initial_phase: int,
    minimum_phase_population: int,
    width: int,
    height: int,
    period: int,
    radius: int = 1,
    limit: int = 100_000,
) -> int:
    """Find a finite contradiction certificate for a proposed phase system."""
    if limit <= 0:
        raise ValueError("limit must be positive")
    for generation in range(1, limit + 1):
        _, required, available = phased_capacity_at_generation(
            substitution,
            initial_phase,
            minimum_phase_population,
            width,
            height,
            period,
            generation,
            radius,
        )
        if required > available:
            return generation
    raise ValueError("no capacity contradiction within the requested limit")
