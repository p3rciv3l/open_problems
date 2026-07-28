from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from itertools import product
from pathlib import Path

from pysat.card import CardEnc, EncType
from pysat.formula import IDPool
from pysat.solvers import Glucose4, Minisat22

from .life import OFFSETS, convex_hull_cells, evolve_finite
from .patterns import Cell, Pattern
from .sat import LifePreimageCNF, finite_counter_predecessor


SYMMETRIES = {"none", "horizontal", "vertical", "rotate180", "d2", "d4"}


class StillLifeCNF:
    """Exact finite-support still-life encoding in a fixed bounding box."""

    def __init__(
        self,
        width: int,
        height: int,
        symmetry: str = "none",
        min_population: int = 1,
        max_population: int | None = None,
    ):
        if width < 1 or height < 1:
            raise ValueError("dimensions must be positive")
        if symmetry not in SYMMETRIES:
            raise ValueError(f"unknown symmetry {symmetry!r}")
        if symmetry == "d4" and width != height:
            raise ValueError("d4 symmetry requires a square box")
        self.width = width
        self.height = height
        self.pool = IDPool()
        self.variables = {
            (x, y): self.pool.id(("target", x, y))
            for y in range(height)
            for x in range(width)
        }
        self.clauses: list[list[int]] = []
        self._encode_still_life()
        self._encode_exact_bounding_box()
        self._encode_symmetry(symmetry)
        variables = list(self.variables.values())
        if min_population > 0:
            self.clauses.extend(
                CardEnc.atleast(
                    variables,
                    min_population,
                    vpool=self.pool,
                    encoding=EncType.seqcounter,
                ).clauses
            )
        if max_population is not None:
            self.clauses.extend(
                CardEnc.atmost(
                    variables,
                    max_population,
                    vpool=self.pool,
                    encoding=EncType.seqcounter,
                ).clauses
            )

    def _variable(self, cell: Cell) -> int | None:
        return self.variables.get(cell)

    def _encode_still_life(self) -> None:
        for y in range(-1, self.height + 1):
            for x in range(-1, self.width + 1):
                cell = (x, y)
                local_cells = [(x + dx, y + dy) for dx, dy in OFFSETS]
                local = [(candidate, self._variable(candidate)) for candidate in local_cells]
                free = [(candidate, var) for candidate, var in local if var is not None]
                for values in product((False, True), repeat=len(free)):
                    assignment = dict(zip((candidate for candidate, _ in free), values))
                    center = assignment.get(cell, False)
                    neighbors = sum(
                        assignment.get(candidate, False)
                        for candidate in local_cells
                        if candidate != cell
                    )
                    evolves_live = neighbors == 3 or (center and neighbors == 2)
                    if evolves_live != center:
                        self.clauses.append(
                            [
                                -var if value else var
                                for (_, var), value in zip(free, values)
                            ]
                        )

    def _encode_exact_bounding_box(self) -> None:
        for side in (
            [(x, 0) for x in range(self.width)],
            [(x, self.height - 1) for x in range(self.width)],
            [(0, y) for y in range(self.height)],
            [(self.width - 1, y) for y in range(self.height)],
        ):
            self.clauses.append([self.variables[cell] for cell in side])

    def _encode_symmetry(self, symmetry: str) -> None:
        transforms = []
        if symmetry in {"horizontal", "d2", "d4"}:
            transforms.append(lambda x, y: (self.width - 1 - x, y))
        if symmetry in {"vertical", "d2", "d4"}:
            transforms.append(lambda x, y: (x, self.height - 1 - y))
        if symmetry in {"rotate180", "d2", "d4"}:
            transforms.append(
                lambda x, y: (self.width - 1 - x, self.height - 1 - y)
            )
        if symmetry == "d4":
            transforms.extend(
                [
                    lambda x, y: (y, x),
                    lambda x, y: (self.width - 1 - y, x),
                ]
            )
        for cell, variable in self.variables.items():
            for transform in transforms:
                other = self.variables[transform(*cell)]
                if variable < other:
                    self.clauses.extend(([-variable, other], [variable, -other]))

    def pattern(self, model: list[int]) -> Pattern:
        positive = {literal for literal in model if literal > 0}
        live = frozenset(
            cell for cell, variable in self.variables.items() if variable in positive
        )
        return Pattern(self.width, self.height, live)

    def block_pattern(self, pattern: Pattern) -> list[int]:
        return [
            -variable if cell in pattern.live else variable
            for cell, variable in self.variables.items()
        ]


@dataclass
class Rejection:
    pattern: Pattern
    cell: Cell
    expected: bool
    predecessor: frozenset[Cell]


def _find_global_rejection(
    pattern: Pattern, goal: str, margin: int
) -> Rejection | None:
    requested = (
        pattern.live
        if goal == "all-live"
        else frozenset(convex_hull_cells(pattern.live))
    )
    for cell in sorted(requested):
        expected = cell in pattern.live
        assignment = finite_counter_predecessor(
            pattern.live,
            pattern.width,
            pattern.height,
            cell,
            expected,
            margin=margin,
        )
        if assignment is None:
            continue
        predecessor = frozenset(
            candidate for candidate, value in assignment.items() if value
        )
        if evolve_finite(predecessor) != pattern.live:
            raise AssertionError("finite counter-predecessor failed direct Life evolution")
        return Rejection(pattern, cell, expected, predecessor)
    globally_quantified = LifePreimageCNF(pattern.assignment)
    with Minisat22(bootstrap_with=globally_quantified.clauses) as solver:
        for cell in sorted(requested):
            expected = cell in pattern.live
            if solver.solve(
                assumptions=[globally_quantified.literal(cell, not expected)]
            ):
                raise RuntimeError(
                    "local countermodel found but no globally valid finite "
                    f"counter-predecessor was found at margin {margin}"
                )
    return None


def _write_dimacs(path: Path, clauses: list[list[int]], variables: int) -> None:
    with path.open("w") as output:
        output.write(f"p cnf {variables} {len(clauses)}\n")
        for clause in clauses:
            output.write(" ".join(map(str, clause)) + " 0\n")


def verify_exhaustion_report(report: dict[str, object]) -> None:
    if report["exhausted"] is not True or report["winner"] is not None:
        raise ValueError("report does not claim exhaustive failure")
    width, height = report["box"]
    master = StillLifeCNF(width, height, report["symmetry"])
    seen: set[frozenset[Cell]] = set()
    for item in report["rejections"]:
        target = frozenset(tuple(cell) for cell in item["target"])
        changed_x, changed_y, expected_integer = item["changed_cell"]
        changed = (changed_x, changed_y)
        expected = bool(expected_integer)
        predecessor = frozenset(tuple(cell) for cell in item["predecessor"])
        pattern = Pattern(width, height, target)
        if evolve_finite(target) != target:
            raise ValueError("rejection target is not a finite still life")
        if target in seen:
            raise ValueError("duplicate rejection target")
        seen.add(target)
        if (changed in target) != expected or (changed in predecessor) == expected:
            raise ValueError("predecessor does not change the claimed target assignment")
        if evolve_finite(predecessor) != target:
            raise ValueError("predecessor does not evolve exactly to its target")
        master.clauses.append(master.block_pattern(pattern))
    with Minisat22(bootstrap_with=master.clauses) as solver:
        if solver.solve():
            raise ValueError("rejection list does not exhaust the stated search class")
    if len(seen) != report["candidates_rejected_by_global_finite_predecessor"]:
        raise ValueError("rejection count does not match manifest")


def export_exhaustion_proof(
    report: dict[str, object], proof_prefix: Path
) -> dict[str, object]:
    verify_exhaustion_report(report)
    width, height = report["box"]
    master = StillLifeCNF(width, height, report["symmetry"])
    for item in report["rejections"]:
        pattern = Pattern(
            width, height, frozenset(tuple(cell) for cell in item["target"])
        )
        master.clauses.append(master.block_pattern(pattern))
    proof_prefix.parent.mkdir(parents=True, exist_ok=True)
    cnf_path = proof_prefix.with_suffix(".cnf")
    drat_path = proof_prefix.with_suffix(".drat")
    _write_dimacs(cnf_path, master.clauses, master.pool.top)
    with Glucose4(bootstrap_with=master.clauses, with_proof=True) as solver:
        if solver.solve():
            raise AssertionError("proof solver did not reproduce UNSAT")
        proof = solver.get_proof()
    if not proof or proof[-1].strip() != "0":
        proof.append("0")
    drat_path.write_text("\n".join(proof) + "\n")
    return {
        "cnf": str(cnf_path),
        "drat": str(drat_path),
        "variables": master.pool.top,
        "clauses": len(master.clauses),
    }


def synthesize(
    width: int,
    height: int,
    goal: str = "all-live",
    symmetry: str = "d2",
    margin: int = 2,
    max_candidates: int | None = None,
    proof_prefix: Path | None = None,
) -> dict[str, object]:
    if goal not in {"all-live", "convex-hull"}:
        raise ValueError(f"unknown goal {goal!r}")
    master = StillLifeCNF(width, height, symmetry)
    rejections: list[Rejection] = []
    exhausted = False
    winner: Pattern | None = None

    with Minisat22(bootstrap_with=master.clauses) as solver:
        while max_candidates is None or len(rejections) < max_candidates:
            if not solver.solve():
                exhausted = True
                break
            pattern = master.pattern(solver.get_model())
            rejection = _find_global_rejection(pattern, goal, margin)
            if rejection is None:
                winner = pattern
                break
            rejections.append(rejection)
            clause = master.block_pattern(pattern)
            master.clauses.append(clause)
            solver.add_clause(clause)

    result: dict[str, object] = {
        "box": [width, height],
        "symmetry": symmetry,
        "goal": goal,
        "finite_predecessor_margin": margin,
        "candidates_rejected_by_global_finite_predecessor": len(rejections),
        "exhausted": exhausted,
        "winner": None
        if winner is None
        else [[x, y] for x, y in sorted(winner.live)],
        "rejections": [
            {
                "target": [[x, y] for x, y in sorted(rejection.pattern.live)],
                "changed_cell": [
                    rejection.cell[0],
                    rejection.cell[1],
                    int(rejection.expected),
                ],
                "predecessor": [
                    [x, y] for x, y in sorted(rejection.predecessor)
                ],
            }
            for rejection in rejections
        ],
    }
    if exhausted and proof_prefix is not None:
        result["proof"] = export_exhaustion_proof(result, proof_prefix)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Enumerate finite still lifes and reject them with global predecessors"
    )
    parser.add_argument("width", type=int, nargs="?")
    parser.add_argument("height", type=int, nargs="?")
    parser.add_argument("--goal", choices=("all-live", "convex-hull"), default="all-live")
    parser.add_argument("--symmetry", choices=sorted(SYMMETRIES), default="d2")
    parser.add_argument("--margin", type=int, default=2)
    parser.add_argument("--max-candidates", type=int)
    parser.add_argument("--proof-prefix", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--verify", type=Path)
    args = parser.parse_args()
    if args.verify:
        verify_exhaustion_report(json.loads(args.verify.read_text()))
        return
    if args.width is None or args.height is None:
        parser.error("width and height are required unless --verify is used")
    result = synthesize(
        args.width,
        args.height,
        args.goal,
        args.symmetry,
        args.margin,
        args.max_candidates,
        args.proof_prefix,
    )
    serialized = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(serialized)
    else:
        print(serialized, end="")


if __name__ == "__main__":
    main()
