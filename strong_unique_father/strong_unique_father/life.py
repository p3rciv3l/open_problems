from __future__ import annotations

from math import gcd

from .patterns import Cell

OFFSETS = tuple(
    (dx, dy) for dy in (-1, 0, 1) for dx in (-1, 0, 1)
)


def life_value(center: bool, neighbors: int) -> bool:
    return neighbors == 3 or (center and neighbors == 2)


def evolve_cell(predecessor: dict[Cell, bool], cell: Cell) -> bool:
    x, y = cell
    center = predecessor[(x, y)]
    neighbors = sum(
        predecessor[(x + dx, y + dy)]
        for dx, dy in OFFSETS
        if (dx, dy) != (0, 0)
    )
    return life_value(center, neighbors)


def verify_image(
    predecessor: dict[Cell, bool], image: dict[Cell, bool]
) -> bool:
    return all(evolve_cell(predecessor, cell) == value for cell, value in image.items())


def evolve_finite(live: frozenset[Cell] | set[Cell]) -> frozenset[Cell]:
    candidates = {
        (x + dx, y + dy)
        for x, y in live
        for dx, dy in OFFSETS
    }
    result = set()
    for x, y in candidates:
        neighbors = sum(
            (x + dx, y + dy) in live
            for dx, dy in OFFSETS
            if (dx, dy) != (0, 0)
        )
        if life_value((x, y) in live, neighbors):
            result.add((x, y))
    return frozenset(result)


def convex_hull_cells(live: frozenset[Cell]) -> set[Cell]:
    points = sorted(live)
    if len(points) <= 1:
        return set(points)
    if len(points) == 2:
        (x1, y1), (x2, y2) = points
        steps = gcd(abs(x2 - x1), abs(y2 - y1))
        dx, dy = (x2 - x1) // steps, (y2 - y1) // steps
        return {(x1 + step * dx, y1 + step * dy) for step in range(steps + 1)}

    def cross(o: Cell, a: Cell, b: Cell) -> int:
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    lower: list[Cell] = []
    for point in points:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], point) <= 0:
            lower.pop()
        lower.append(point)
    upper: list[Cell] = []
    for point in reversed(points):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], point) <= 0:
            upper.pop()
        upper.append(point)
    hull = lower[:-1] + upper[:-1]

    min_x, max_x = min(x for x, _ in hull), max(x for x, _ in hull)
    min_y, max_y = min(y for _, y in hull), max(y for _, y in hull)

    def inside(point: Cell) -> bool:
        signs = [
            cross(hull[i], hull[(i + 1) % len(hull)], point)
            for i in range(len(hull))
        ]
        return all(value >= 0 for value in signs) or all(value <= 0 for value in signs)

    return {
        (x, y)
        for y in range(min_y, max_y + 1)
        for x in range(min_x, max_x + 1)
        if inside((x, y))
    }
