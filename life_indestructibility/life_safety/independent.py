from collections.abc import Iterable

from .life import Cell, Pattern, bounding_box


def dense_step(pattern: Iterable[Cell]) -> Pattern:
    """Independent direct-array Life step used to check sparse/SAT traces."""
    alive = frozenset(pattern)
    if not alive:
        return frozenset()
    xmin, xmax, ymin, ymax = bounding_box(alive)
    output: set[Cell] = set()
    for x in range(xmin - 1, xmax + 2):
        for y in range(ymin - 1, ymax + 2):
            neighbors = 0
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    if (dx, dy) != (0, 0) and (x + dx, y + dy) in alive:
                        neighbors += 1
            if neighbors == 3 or (neighbors == 2 and (x, y) in alive):
                output.add((x, y))
    return frozenset(output)


def verify_exact_period(
    initial: Iterable[Cell],
    repeat_generation: int,
    period: int,
    expected_repeat: Iterable[Cell] | None = None,
) -> bool:
    """Replay an exact global period certificate on the unbounded sparse plane."""
    if repeat_generation < 1 or period < 1 or period > repeat_generation:
        return False
    current = frozenset(initial)
    earlier = current if repeat_generation == period else None
    for generation in range(1, repeat_generation + 1):
        current = dense_step(current)
        if generation == repeat_generation - period:
            earlier = current
    return current == earlier and (
        expected_repeat is None or current == frozenset(expected_repeat)
    )
