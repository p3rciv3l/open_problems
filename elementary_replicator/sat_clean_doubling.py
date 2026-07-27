"""Z3 exclusion search for exact clean two-copy events in B3/S23."""

import argparse
import csv
from dataclasses import dataclass
from itertools import combinations
from pathlib import Path

from z3 import And, Bool, If, Not, Or, Solver, Sum, sat

Cell = tuple[int, int]
CSV_FIELDS = ("width", "height", "time", "offset_pairs", "status")


@dataclass(frozen=True)
class ScopeResult:
    width: int
    height: int
    time: int
    offset_pairs: int
    satisfiable: bool


def _domain(width: int, height: int, time: int) -> list[Cell]:
    return [
        (x, y)
        for y in range(-time, height + time)
        for x in range(-time, width + time)
    ]


def _boxes_disjoint(a: Cell, b: Cell, width: int, height: int) -> bool:
    return (
        a[0] + width <= b[0]
        or b[0] + width <= a[0]
        or a[1] + height <= b[1]
        or b[1] + height <= a[1]
    )


def _lex_le(left, right):
    less_at = []
    equal_prefix = []
    for a, b in zip(left, right):
        less_at.append(And(*(equal_prefix + [Not(a), b])))
        equal_prefix.append(a == b)
    return Or(*(less_at + [And(*equal_prefix)]))


def exclude_scope(width: int, height: int, time: int) -> ScopeResult:
    """Search one minimal-box/time scope; return SAT if a witness exists.

    The seed touches all four sides of its `width` by `height` box. At `time`
    the entire infinite configuration must be exactly two translated seed
    copies whose bounding boxes are disjoint. Initial horizontal and vertical
    reflections are reduced by lex-leader constraints.
    """
    if width <= 0 or height <= 0 or time <= 0:
        raise ValueError("scope dimensions and time must be positive")

    layers = [
        {
            cell: Bool(f"cell_{t}_{cell[0]}_{cell[1]}")
            for cell in _domain(width, height, t)
        }
        for t in range(time + 1)
    ]
    solver = Solver()
    initial = layers[0]
    solver.add(
        Or(*(initial[x, 0] for x in range(width))),
        Or(*(initial[x, height - 1] for x in range(width))),
        Or(*(initial[0, y] for y in range(height))),
        Or(*(initial[width - 1, y] for y in range(height))),
    )

    order = [(x, y) for y in range(height) for x in range(width)]
    bits = [initial[cell] for cell in order]
    transforms = (
        lambda x, y: (width - 1 - x, y),
        lambda x, y: (x, height - 1 - y),
        lambda x, y: (width - 1 - x, height - 1 - y),
    )
    for transform in transforms:
        solver.add(_lex_le(bits, [initial[transform(*cell)] for cell in order]))

    for t in range(time):
        previous, following = layers[t], layers[t + 1]
        for (x, y), cell in following.items():
            neighbors = [
                previous.get((x + dx, y + dy), False)
                for dy in (-1, 0, 1)
                for dx in (-1, 0, 1)
                if (dx, dy) != (0, 0)
            ]
            count = Sum(*(If(neighbor, 1, 0) for neighbor in neighbors))
            solver.add(
                cell
                == Or(
                    count == 3,
                    And(previous.get((x, y), False), count == 2),
                )
            )

    offsets = [
        (x, y)
        for y in range(-time, time + 1)
        for x in range(-time, time + 1)
    ]
    pairs = [
        pair
        for pair in combinations(offsets, 2)
        if _boxes_disjoint(*pair, width, height)
    ]
    for first, second in pairs:
        solver.push()
        for (x, y), terminal in layers[time].items():
            sources = [
                initial[source]
                for dx, dy in (first, second)
                if (source := (x - dx, y - dy)) in initial
            ]
            solver.add(terminal == (Or(*sources) if sources else False))
        if solver.check() == sat:
            return ScopeResult(width, height, time, len(pairs), True)
        solver.pop()
    return ScopeResult(width, height, time, len(pairs), False)


def search(max_side: int, max_time: int) -> list[ScopeResult]:
    """Search all boxes up to rotation, with reflection symmetry reduction."""
    if max_side <= 0 or max_time <= 0:
        raise ValueError("max_side and max_time must be positive")
    return [
        exclude_scope(width, height, time)
        for width in range(1, max_side + 1)
        for height in range(1, width + 1)
        for time in range(1, max_time + 1)
    ]


def _positive_int(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be positive")
    return parsed


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-side", type=_positive_int, default=4)
    parser.add_argument("--max-time", type=_positive_int, default=2)
    parser.add_argument("--csv", type=Path)
    args = parser.parse_args()
    results = search(args.max_side, args.max_time)
    rows = [
        {
            "width": result.width,
            "height": result.height,
            "time": result.time,
            "offset_pairs": result.offset_pairs,
            "status": "SAT" if result.satisfiable else "UNSAT",
        }
        for result in results
    ]
    if args.csv:
        with args.csv.open("w", newline="") as output:
            writer = csv.DictWriter(output, fieldnames=CSV_FIELDS)
            writer.writeheader()
            writer.writerows(rows)
    for row in rows:
        print(
            f"{row['width']}x{row['height']} T={row['time']} "
            f"pairs={row['offset_pairs']} {row['status']}"
        )


if __name__ == "__main__":
    main()
