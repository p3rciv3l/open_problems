from __future__ import annotations

from itertools import product

from pysat.card import CardEnc, EncType
from pysat.formula import IDPool

from .life import OFFSETS, life_value
from .patterns import Cell


class LifePreimageCNF:
    def __init__(self, image: dict[Cell, bool], encoding: str = "cardinality"):
        if encoding not in {"cardinality", "truth-table"}:
            raise ValueError(f"unknown encoding {encoding!r}")
        self.image = image
        self.domain = {
            (x + dx, y + dy)
            for x, y in image
            for dx, dy in OFFSETS
        }
        self.pool = IDPool()
        self.variables = {cell: self.pool.id(("cell", cell)) for cell in sorted(self.domain)}
        self.clauses: list[list[int]] = []
        if encoding == "cardinality":
            self._encode_cardinality()
        else:
            self._encode_truth_table()

    def _local_variables(self, cell: Cell) -> list[int]:
        x, y = cell
        return [self.variables[(x + dx, y + dy)] for dx, dy in OFFSETS]

    def _encode_truth_table(self) -> None:
        for cell, expected in self.image.items():
            variables = self._local_variables(cell)
            for values in product((False, True), repeat=9):
                center = values[4]
                neighbors = sum(values) - center
                if life_value(center, neighbors) != expected:
                    self.clauses.append(
                        [-var if value else var for var, value in zip(variables, values)]
                    )

    def _encode_cardinality(self) -> None:
        for cell, expected in self.image.items():
            local = self._local_variables(cell)
            center = local[4]
            neighbors = local[:4] + local[5:]
            if expected:
                self._conditional_count(neighbors, 3, 3, [center])
                self._conditional_count(neighbors, 2, 3, [-center])
            else:
                dead_center_split = self.pool.id(("dead-center-split", cell))
                self._conditional_count(
                    neighbors, 0, 2, [center, -dead_center_split]
                )
                self._conditional_count(
                    neighbors, 4, 8, [center, dead_center_split]
                )
                live_center_split = self.pool.id(("live-center-split", cell))
                self._conditional_count(
                    neighbors, 0, 1, [-center, -live_center_split]
                )
                self._conditional_count(
                    neighbors, 4, 8, [-center, live_center_split]
                )

    def _conditional_count(
        self, literals: list[int], lower: int, upper: int, prefix: list[int]
    ) -> None:
        clauses: list[list[int]] = []
        if lower:
            clauses.extend(
                CardEnc.atleast(
                    literals, lower, vpool=self.pool, encoding=EncType.seqcounter
                ).clauses
            )
        if upper < len(literals):
            clauses.extend(
                CardEnc.atmost(
                    literals, upper, vpool=self.pool, encoding=EncType.seqcounter
                ).clauses
            )
        self.clauses.extend([prefix + clause for clause in clauses])

    def literal(self, cell: Cell, value: bool) -> int:
        variable = self.variables[cell]
        return variable if value else -variable

    def model_assignment(self, model: list[int]) -> dict[Cell, bool]:
        positive = {literal for literal in model if literal > 0}
        return {cell: variable in positive for cell, variable in self.variables.items()}


def finite_counter_predecessor(
    image_live: frozenset[Cell],
    width: int,
    height: int,
    cell: Cell,
    expected: bool,
    margin: int = 2,
    encoding: str = "cardinality",
) -> dict[Cell, bool] | None:
    """Find a finite-support, globally valid predecessor changing one cell."""
    if margin < 0:
        raise ValueError("margin must be nonnegative")
    support = {
        (x, y)
        for y in range(-margin, height + margin)
        for x in range(-margin, width + margin)
    }
    image = {
        (x, y): (x, y) in image_live
        for y in range(-margin - 1, height + margin + 1)
        for x in range(-margin - 1, width + margin + 1)
    }
    cnf = LifePreimageCNF(image, encoding)
    assumptions = [cnf.literal(cell, not expected)]
    assumptions.extend(
        cnf.literal(candidate, False)
        for candidate in sorted(cnf.domain - support)
    )

    from pysat.solvers import Cadical195

    with Cadical195(bootstrap_with=cnf.clauses) as solver:
        if not solver.solve(assumptions=assumptions):
            return None
        assignment = cnf.model_assignment(solver.get_model())
    return {candidate: value for candidate, value in assignment.items() if candidate in support}
