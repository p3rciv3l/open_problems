"""SAT search for a Life tile implementing a one-dimensional macro rule."""

import argparse
from dataclasses import dataclass

from z3 import And, Bool, If, Not, Or, Solver, Sum, sat

Cell = tuple[int, int]
PARITY_RULES = (60, 90, 102, 150)


@dataclass(frozen=True)
class MacroGeometry:
    width: int
    height: int
    pitch: int
    time: int

    def validate(self) -> None:
        if min(self.width, self.height, self.pitch, self.time) <= 0:
            raise ValueError("geometry values must be positive")
        if self.pitch < self.width:
            raise ValueError("pitch must be at least the tile width")
        if not outside_context_is_excluded(self):
            raise ValueError("time cone reaches macro sites outside the context")


@dataclass(frozen=True)
class MacroResult:
    geometry: MacroGeometry
    rule: int
    satisfiable: bool
    tile: frozenset[Cell] | None


def _window(geometry: MacroGeometry) -> tuple[int, int]:
    left = -((geometry.pitch - geometry.width) // 2)
    return left, left + geometry.pitch - 1


def outside_context_is_excluded(geometry: MacroGeometry) -> bool:
    """Whether sites beyond {-1,0,1} cannot affect the central window."""
    left, right = _window(geometry)
    left_outside_right = -2 * geometry.pitch + geometry.width - 1
    right_outside_left = 2 * geometry.pitch
    distance = min(
        left - left_outside_right,
        right_outside_left - right,
    )
    return distance > geometry.time


def _domain(geometry: MacroGeometry, layer: int) -> list[Cell]:
    remaining = geometry.time - layer
    left, right = _window(geometry)
    return [
        (x, y)
        for y in range(
            -geometry.time - remaining,
            geometry.height + geometry.time + remaining,
        )
        for x in range(left - remaining, right + remaining + 1)
    ]


def _lex_le(left, right):
    less_at = []
    equal_prefix = []
    for a, b in zip(left, right):
        less_at.append(And(*(equal_prefix + [Not(a), b])))
        equal_prefix.append(a == b)
    return Or(*(less_at + [And(*equal_prefix)]))


def _rule_output(rule: int, context: int) -> bool:
    return bool((rule >> context) & 1)


def solve_macro_rule(geometry: MacroGeometry, rule: int) -> MacroResult:
    """Find one tile satisfying every local truth-table row, or prove UNSAT."""
    geometry.validate()
    if not 0 <= rule <= 255 or rule & 1:
        raise ValueError("rule must be an ECA rule with 000 -> 0")

    solver = Solver()
    tile = {
        (x, y): Bool(f"tile_{x}_{y}")
        for y in range(geometry.height)
        for x in range(geometry.width)
    }
    solver.add(
        Or(*(tile[x, 0] for x in range(geometry.width))),
        Or(*(tile[x, geometry.height - 1] for x in range(geometry.width))),
        Or(*(tile[0, y] for y in range(geometry.height))),
        Or(*(tile[geometry.width - 1, y] for y in range(geometry.height))),
    )
    order = [
        (x, y)
        for y in range(geometry.height)
        for x in range(geometry.width)
    ]
    solver.add(
        _lex_le(
            [tile[cell] for cell in order],
            [tile[x, geometry.height - 1 - y] for x, y in order],
        )
    )
    if rule in (90, 150):
        solver.add(
            _lex_le(
                [tile[cell] for cell in order],
                [tile[geometry.width - 1 - x, y] for x, y in order],
            )
        )

    for context in range(1, 8):
        layers = []
        initial = {}
        for x, y in _domain(geometry, 0):
            sources = []
            for bit, site in ((4, -1), (2, 0), (1, 1)):
                source = (x - site * geometry.pitch, y)
                if context & bit and source in tile:
                    sources.append(tile[source])
            initial[x, y] = Or(*sources) if sources else False
        layers.append(initial)
        for layer in range(1, geometry.time + 1):
            layers.append(
                {
                    cell: Bool(
                        f"c_{context}_{layer}_{cell[0]}_{cell[1]}"
                    )
                    for cell in _domain(geometry, layer)
                }
            )

        for layer in range(geometry.time):
            previous, following = layers[layer], layers[layer + 1]
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

        output_live = _rule_output(rule, context)
        for cell, value in layers[-1].items():
            expected = tile.get(cell, False) if output_live else False
            solver.add(value == expected)

    if solver.check() != sat:
        return MacroResult(geometry, rule, False, None)
    model = solver.model()
    witness = frozenset(
        cell for cell, value in tile.items() if model.eval(value)
    )
    return MacroResult(geometry, rule, True, witness)


def search(
    *,
    max_width: int,
    max_height: int,
    gaps: tuple[int, ...],
    extra_times: int,
    rules: tuple[int, ...] = PARITY_RULES,
) -> list[MacroResult]:
    if min(max_width, max_height, extra_times + 1) <= 0:
        raise ValueError("search bounds must be positive")
    if not gaps or any(gap < 0 for gap in gaps):
        raise ValueError("gaps must be a nonempty tuple of nonnegative values")
    results = []
    for width in range(1, max_width + 1):
        for height in range(1, max_height + 1):
            for gap in gaps:
                pitch = width + gap
                for time in range(pitch, pitch + extra_times + 1):
                    geometry = MacroGeometry(width, height, pitch, time)
                    if not outside_context_is_excluded(geometry):
                        continue
                    for rule in rules:
                        results.append(solve_macro_rule(geometry, rule))
    return results


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-width", type=int, default=3)
    parser.add_argument("--max-height", type=int, default=3)
    parser.add_argument("--gap", type=int, action="append")
    parser.add_argument("--extra-times", type=int, default=1)
    args = parser.parse_args()
    results = search(
        max_width=args.max_width,
        max_height=args.max_height,
        gaps=tuple(args.gap or [1]),
        extra_times=args.extra_times,
    )
    for result in results:
        geometry = result.geometry
        status = "SAT" if result.satisfiable else "UNSAT"
        print(
            f"rule={result.rule} tile={geometry.width}x{geometry.height} "
            f"pitch={geometry.pitch} T={geometry.time} {status}"
        )


if __name__ == "__main__":
    main()
