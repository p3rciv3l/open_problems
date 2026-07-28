"""Finite-speed obstructions to fixed-period branching."""

from collections.abc import Sequence


def light_cone_capacity(
    width: int,
    height: int,
    elapsed: int,
    radius: int = 1,
) -> int:
    """Return the number of sites in the rectangular causal bound."""
    if min(width, height) <= 0 or min(elapsed, radius) < 0:
        raise ValueError("sizes must be positive and times nonnegative")
    reach = radius * elapsed
    return (width + 2 * reach) * (height + 2 * reach)


def minimum_elapsed_time_for_copies(
    width: int,
    height: int,
    copies: int,
    radius: int = 1,
) -> int:
    """Return the least integer time whose causal bound can hold the copies."""
    if min(width, height, copies, radius) <= 0:
        raise ValueError("all arguments must be positive")
    low = 0
    high = 1
    while light_cone_capacity(width, height, high, radius) < copies:
        high *= 2
    while low < high:
        middle = (low + high) // 2
        if light_cone_capacity(width, height, middle, radius) >= copies:
            high = middle
        else:
            low = middle + 1
    return low


def forced_lineage_cancellations(
    nominal_lineages: int,
    maximum_lineages_per_tile: int,
    width: int,
    height: int,
    elapsed: int,
    radius: int = 1,
) -> int:
    """Lower-bound nominal lineages absent from any endpoint macrotile."""
    if min(nominal_lineages, maximum_lineages_per_tile) <= 0:
        raise ValueError("lineage counts must be positive")
    capacity = light_cone_capacity(width, height, elapsed, radius)
    return max(0, nominal_lineages - maximum_lineages_per_tile * capacity)


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
    available = light_cone_capacity(width, height, period * generation)
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
    available = light_cone_capacity(
        width, height, period * generation, radius
    )
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
