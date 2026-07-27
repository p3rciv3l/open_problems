"""A small independent B3/S23 simulator on the infinite square grid."""

from collections import Counter
from collections.abc import Iterable

Cell = tuple[int, int]
Pattern = frozenset[Cell]

NEIGHBORS = tuple(
    (dx, dy)
    for dy in (-1, 0, 1)
    for dx in (-1, 0, 1)
    if (dx, dy) != (0, 0)
)


def step(pattern: Iterable[Cell]) -> Pattern:
    live = frozenset(pattern)
    counts = Counter(
        (x + dx, y + dy)
        for x, y in live
        for dx, dy in NEIGHBORS
    )
    return frozenset(
        cell
        for cell, count in counts.items()
        if count == 3 or (count == 2 and cell in live)
    )


def evolve(pattern: Iterable[Cell], generations: int) -> Pattern:
    if generations < 0:
        raise ValueError("generations must be nonnegative")
    result = frozenset(pattern)
    for _ in range(generations):
        result = step(result)
    return result


def translate(pattern: Iterable[Cell], offset: Cell) -> Pattern:
    dx, dy = offset
    return frozenset((x + dx, y + dy) for x, y in pattern)


def reflect_y(pattern: Iterable[Cell]) -> Pattern:
    return frozenset((x, -y) for x, y in pattern)
