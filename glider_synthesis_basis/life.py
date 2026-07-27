"""Small, unbounded-plane Conway Life simulator."""
from collections import Counter
from collections.abc import Iterable

Cell = tuple[int, int]
Pattern = frozenset[Cell]
_NEIGHBOURS = tuple(
    (dx, dy)
    for dx in (-1, 0, 1)
    for dy in (-1, 0, 1)
    if (dx, dy) != (0, 0)
)


def step(cells: Iterable[Cell]) -> Pattern:
    live = frozenset(cells)
    counts = Counter(
        (x + dx, y + dy)
        for x, y in live
        for dx, dy in _NEIGHBOURS
    )
    return frozenset(
        cell for cell, count in counts.items()
        if count == 3 or (count == 2 and cell in live)
    )


def run(cells: Iterable[Cell], generations: int) -> Pattern:
    if generations < 0:
        raise ValueError("generations must be non-negative")
    state = frozenset(cells)
    for _ in range(generations):
        state = step(state)
    return state


def trajectory(cells: Iterable[Cell], generations: int) -> tuple[Pattern, ...]:
    state = frozenset(cells)
    states = [state]
    for _ in range(generations):
        state = step(state)
        states.append(state)
    return tuple(states)


def is_still_life(cells: Iterable[Cell]) -> bool:
    pattern = frozenset(cells)
    return step(pattern) == pattern


def translate(cells: Iterable[Cell], dx: int, dy: int) -> Pattern:
    return frozenset((x + dx, y + dy) for x, y in cells)
