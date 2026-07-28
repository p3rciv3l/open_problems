from collections import Counter
from collections.abc import Iterable

Cell = tuple[int, int]
Pattern = frozenset[Cell]

NEIGHBORS = tuple(
    (dx, dy)
    for dx in (-1, 0, 1)
    for dy in (-1, 0, 1)
    if (dx, dy) != (0, 0)
)


def step(pattern: Iterable[Cell]) -> Pattern:
    alive = frozenset(pattern)
    counts: Counter[Cell] = Counter()
    for x, y in alive:
        for dx, dy in NEIGHBORS:
            counts[x + dx, y + dy] += 1
    return frozenset(
        cell
        for cell, count in counts.items()
        if count == 3 or (count == 2 and cell in alive)
    )


def evolve(pattern: Iterable[Cell], generations: int) -> list[Pattern]:
    history = [frozenset(pattern)]
    for _ in range(generations):
        history.append(step(history[-1]))
    return history


def bounding_box(pattern: Iterable[Cell]) -> tuple[int, int, int, int]:
    cells = tuple(pattern)
    if not cells:
        raise ValueError("an empty pattern has no bounding box")
    xs = [cell[0] for cell in cells]
    ys = [cell[1] for cell in cells]
    return min(xs), max(xs), min(ys), max(ys)


def translate(pattern: Iterable[Cell], dx: int, dy: int) -> Pattern:
    return frozenset((x + dx, y + dy) for x, y in pattern)


def serialize(pattern: Iterable[Cell]) -> list[list[int]]:
    return [list(cell) for cell in sorted(pattern)]
