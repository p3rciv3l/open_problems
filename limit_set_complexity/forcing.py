#!/usr/bin/env python3
"""Finite SAT checks for the köynnös backward-forcing witness."""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, Iterator

from pysat.solvers import Solver


KOYNNOS = (
    (1, 1, 1, 0, 0, 0),
    (0, 1, 0, 1, 1, 1),
    (0, 0, 0, 0, 1, 0),
)
TARGET_WIDTH = 30
TARGET_HEIGHT = 27
PRE_X = range(-1, TARGET_WIDTH + 1)
PRE_Y = range(-1, TARGET_HEIGHT + 1)
CENTER_TILE = tuple(
    (x, y) for y in range(12, 15) for x in range(12, 18)
)
OFFSETS = tuple(itertools.product((-1, 0, 1), repeat=2))


def agar_value(x: int, y: int, phase_x: int = 0, phase_y: int = 0) -> int:
    return KOYNNOS[(y + phase_y) % 3][(x + phase_x) % 6]


def life(center: int, neighbors: Iterable[int]) -> int:
    count = sum(neighbors)
    return int(count == 3 or (center == 1 and count == 2))


def variable(x: int, y: int) -> int:
    if x not in PRE_X or y not in PRE_Y:
        raise ValueError(f"predecessor coordinate outside domain: {(x, y)}")
    return (y - PRE_Y.start) * len(PRE_X) + (x - PRE_X.start) + 1


def coordinate(var: int) -> tuple[int, int]:
    index = var - 1
    return (index % len(PRE_X) + PRE_X.start, index // len(PRE_X) + PRE_Y.start)


def local_forbidden_clauses(x: int, y: int, output: int) -> Iterator[list[int]]:
    variables = [variable(x + dx, y + dy) for dx, dy in OFFSETS]
    center_index = OFFSETS.index((0, 0))
    for bits in itertools.product((0, 1), repeat=9):
        center = bits[center_index]
        neighbors = bits[:center_index] + bits[center_index + 1 :]
        if life(center, neighbors) != output:
            yield [-var if bit else var for var, bit in zip(variables, bits)]


def instance_clauses(phase_x: int = 0, phase_y: int = 0) -> Iterator[list[int]]:
    for y in range(TARGET_HEIGHT):
        for x in range(TARGET_WIDTH):
            yield from local_forbidden_clauses(
                x, y, agar_value(x, y, phase_x, phase_y)
            )


def expected_predecessor(phase_x: int = 0, phase_y: int = 0) -> list[int]:
    return [
        variable(x, y) if agar_value(x, y, phase_x, phase_y) else -variable(x, y)
        for y in PRE_Y
        for x in PRE_X
    ]


def clause_count(phase_x: int = 0, phase_y: int = 0) -> int:
    return sum(1 for _ in instance_clauses(phase_x, phase_y))


@dataclass(frozen=True)
class PhaseResult:
    phase: tuple[int, int]
    variables: int
    clauses: int
    baseline_sat: bool
    forced_cells: int
    opposite_queries_unsat: int


def verify_phase(
    phase_x: int, phase_y: int, solver_name: str = "cadical195"
) -> PhaseResult:
    encoded_clauses = sum(
        372 if agar_value(x, y, phase_x, phase_y) else 140
        for y in range(TARGET_HEIGHT)
        for x in range(TARGET_WIDTH)
    )
    clauses = instance_clauses(phase_x, phase_y)
    with Solver(name=solver_name, bootstrap_with=clauses) as solver:
        baseline_sat = solver.solve()
        forced = 0
        unsat = 0
        for x, y in CENTER_TILE:
            expected = agar_value(x, y, phase_x, phase_y)
            opposite = variable(x, y) if expected == 0 else -variable(x, y)
            if not solver.solve(assumptions=[opposite]):
                forced += 1
                unsat += 1
        return PhaseResult(
            phase=(phase_x, phase_y),
            variables=len(PRE_X) * len(PRE_Y),
            clauses=encoded_clauses,
            baseline_sat=baseline_sat,
            forced_cells=forced,
            opposite_queries_unsat=unsat,
        )


def verify_all_phases(solver_name: str = "cadical195") -> dict:
    results = [
        verify_phase(px, py, solver_name)
        for py in range(3)
        for px in range(6)
    ]
    passed = all(
        result.baseline_sat
        and result.forced_cells == len(CENTER_TILE)
        and result.opposite_queries_unsat == len(CENTER_TILE)
        for result in results
    )
    return {
        "claim": (
            "Every 30x27 phase of the 6x3-periodic koynnos target forces "
            "the matching central 6x3 predecessor tile."
        ),
        "scope": {
            "target": [TARGET_WIDTH, TARGET_HEIGHT],
            "predecessor": [len(PRE_X), len(PRE_Y)],
            "phases": 18,
            "queried_cells_per_phase": len(CENTER_TILE),
            "time_steps": 1,
        },
        "solver": solver_name,
        "passed": passed,
        "results": [asdict(result) for result in results],
    }


def write_dimacs(
    path: Path, phase_x: int, phase_y: int, cell: tuple[int, int]
) -> str:
    x, y = cell
    expected = agar_value(x, y, phase_x, phase_y)
    opposite = variable(x, y) if expected == 0 else -variable(x, y)
    clauses = list(instance_clauses(phase_x, phase_y))
    clauses.append([opposite])
    header = f"p cnf {len(PRE_X) * len(PRE_Y)} {len(clauses)}\n"
    body = "".join(" ".join(map(str, clause)) + " 0\n" for clause in clauses)
    data = (header + body).encode()
    path.write_bytes(data)
    return hashlib.sha256(data).hexdigest()


def parse_pair(value: str) -> tuple[int, int]:
    parts = value.split(",")
    if len(parts) != 2:
        raise argparse.ArgumentTypeError("expected X,Y")
    return int(parts[0]), int(parts[1])


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--solver", default="cadical195")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--emit-cnf", type=Path)
    parser.add_argument("--phase", type=parse_pair, default=(0, 0))
    parser.add_argument("--cell", type=parse_pair, default=(12, 12))
    args = parser.parse_args()

    if args.emit_cnf:
        digest = write_dimacs(args.emit_cnf, *args.phase, args.cell)
        print(json.dumps({"path": str(args.emit_cnf), "sha256": digest}, indent=2))
        return 0

    report = verify_all_phases(args.solver)
    rendered = json.dumps(report, indent=2)
    if args.output:
        args.output.write_text(rendered + "\n")
    print(rendered)
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
