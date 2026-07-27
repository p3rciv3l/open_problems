from __future__ import annotations

from dataclasses import asdict, dataclass

from pysat.solvers import Cadical195, Minisat22

from .life import convex_hull_cells, verify_image
from .patterns import Cell, Pattern
from .sat import LifePreimageCNF


@dataclass(frozen=True)
class Metric:
    requested: int
    forced: int

    @property
    def fraction(self) -> float:
        return self.forced / self.requested if self.requested else 1.0

    @property
    def complete(self) -> bool:
        return self.forced == self.requested


def _serialized_assignment(assignment: dict[Cell, bool]) -> list[list[int]]:
    return [[x, y, int(value)] for (x, y), value in sorted(assignment.items())]


def analyze_stabilization(
    pattern: Pattern, independent: bool = False
) -> dict[str, object]:
    image = pattern.assignment
    primary = LifePreimageCNF(image, "cardinality")
    requested = pattern.live | convex_hull_cells(pattern.live)
    forced: set[Cell] = set()
    counter_predecessors: dict[str, list[list[int]]] = {}

    with Minisat22(bootstrap_with=primary.clauses) as solver:
        if not solver.solve():
            raise ValueError("image patch has no predecessor")
        for cell in sorted(requested):
            expected = image[cell]
            opposite = primary.literal(cell, not expected)
            if solver.solve(assumptions=[opposite]):
                witness = primary.model_assignment(solver.get_model())
                if witness[cell] == expected or not verify_image(witness, image):
                    raise AssertionError("SAT backend returned an invalid counter-predecessor")
                counter_predecessors[f"{cell[0]},{cell[1]}"] = _serialized_assignment(witness)
            else:
                forced.add(cell)

    independently_verified = False
    if independent:
        check = LifePreimageCNF(image, "truth-table")
        with Cadical195(bootstrap_with=check.clauses) as solver:
            for cell in sorted(forced):
                if solver.solve(assumptions=[check.literal(cell, not image[cell])]):
                    raise AssertionError(f"independent encoding refuted forced cell {cell}")
        independently_verified = True

    live_metric = Metric(len(pattern.live), len(pattern.live & forced))
    hull = convex_hull_cells(pattern.live)
    hull_metric = Metric(len(hull), len(hull & forced))
    return {
        "claim_scope": {
            "image_rectangle": [pattern.width, pattern.height],
            "predecessor_halo": [
                -1,
                pattern.width,
                -1,
                pattern.height,
            ],
            "arbitrary_global_predecessor_covered": True,
            "reason": (
                "Every global predecessor restricts to a satisfying halo assignment; "
                "outside cells cannot affect this image rectangle."
            ),
            "strong_unique_father_solved": False,
        },
        "population": len(pattern.live),
        "live_cells": {**asdict(live_metric), "fraction": live_metric.fraction, "complete": live_metric.complete},
        "convex_hull_assignment": {
            **asdict(hull_metric),
            "fraction": hull_metric.fraction,
            "complete": hull_metric.complete,
        },
        "forced_cells": [[x, y, int(image[x, y])] for x, y in sorted(forced)],
        "counter_predecessors": counter_predecessors,
        "independently_verified": independently_verified,
    }
