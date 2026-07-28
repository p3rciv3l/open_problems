#!/usr/bin/env python3
"""Search finite marching-band patches for a two-step expanding cap."""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, Iterator, Sequence

from pysat.formula import CNF
from pysat.solvers import Solver

from forcing import OFFSETS, life


MARCHING_BAND = (
    (1, 0, 0, 0, 0, 0, 1, 0),
    (1, 1, 0, 0, 1, 1, 0, 0),
    (1, 1, 0, 0, 1, 1, 0, 0),
    (0, 0, 1, 0, 1, 0, 0, 0),
)


def band_value(x: int, y: int, phase_x: int = 0, phase_y: int = 0) -> int:
    return MARCHING_BAND[(y + phase_y) % 4][(x + phase_x) % 8]


@dataclass(frozen=True)
class Domain:
    width: int
    height: int

    @property
    def middle_x(self) -> range:
        return range(-1, self.width + 1)

    @property
    def middle_y(self) -> range:
        return range(-1, self.height + 1)

    @property
    def predecessor_x(self) -> range:
        return range(-2, self.width + 2)

    @property
    def predecessor_y(self) -> range:
        return range(-2, self.height + 2)

    @property
    def predecessor_variables(self) -> int:
        return len(self.predecessor_x) * len(self.predecessor_y)

    @property
    def variables(self) -> int:
        return self.predecessor_variables + len(self.middle_x) * len(self.middle_y)

    def predecessor_var(self, x: int, y: int) -> int:
        if x not in self.predecessor_x or y not in self.predecessor_y:
            raise ValueError((x, y))
        return (
            (y - self.predecessor_y.start) * len(self.predecessor_x)
            + x
            - self.predecessor_x.start
            + 1
        )

    def middle_var(self, x: int, y: int) -> int:
        if x not in self.middle_x or y not in self.middle_y:
            raise ValueError((x, y))
        return (
            self.predecessor_variables
            + (y - self.middle_y.start) * len(self.middle_x)
            + x
            - self.middle_x.start
            + 1
        )


def relation_clauses(inputs: list[int], output: int) -> Iterator[list[int]]:
    center_index = OFFSETS.index((0, 0))
    for bits in itertools.product((0, 1), repeat=9):
        result = life(
            bits[center_index], bits[:center_index] + bits[center_index + 1 :]
        )
        clause = [-var if bit else var for var, bit in zip(inputs, bits)]
        clause.append(output if result else -output)
        yield clause


def fixed_output_clauses(inputs: list[int], output: int) -> Iterator[list[int]]:
    center_index = OFFSETS.index((0, 0))
    for bits in itertools.product((0, 1), repeat=9):
        result = life(
            bits[center_index], bits[:center_index] + bits[center_index + 1 :]
        )
        if result != output:
            yield [-var if bit else var for var, bit in zip(inputs, bits)]


def instance_clauses(
    domain: Domain, phase_x: int = 0, phase_y: int = 0
) -> Iterator[list[int]]:
    for y in domain.middle_y:
        for x in domain.middle_x:
            inputs = [
                domain.predecessor_var(x + dx, y + dy) for dx, dy in OFFSETS
            ]
            yield from relation_clauses(inputs, domain.middle_var(x, y))
    for y in range(domain.height):
        for x in range(domain.width):
            inputs = [domain.middle_var(x + dx, y + dy) for dx, dy in OFFSETS]
            yield from fixed_output_clauses(
                inputs, band_value(x, y, phase_x, phase_y)
            )


def cap_cells(domain: Domain) -> tuple[tuple[int, int], ...]:
    return tuple(
        (x, y)
        for y in range(-1, domain.height + 1)
        for x in range(10, domain.width - 18)
    )


@dataclass(frozen=True)
class CandidateResult:
    padding: int
    phase: tuple[int, int]
    output_size: tuple[int, int]
    predecessor_size: tuple[int, int]
    variables: int
    clauses: int
    baseline_sat: bool
    queried_cells: int
    forced_cells: int
    expanded_rows_forced: bool
    canonical_interior_forced: bool
    first_failure: tuple[int, int] | None
    success: bool


def dimensions(padding: int) -> Domain:
    return Domain(2 * padding + 8, 2 * padding + 4)


def clause_count(domain: Domain, phase_x: int = 0, phase_y: int = 0) -> int:
    relation_count = len(domain.middle_x) * len(domain.middle_y) * 512
    fixed_count = sum(
        372 if band_value(x, y, phase_x, phase_y) else 140
        for y in range(domain.height)
        for x in range(domain.width)
    )
    return relation_count + fixed_count


def verify_candidate(
    padding: int,
    phase_x: int = 0,
    phase_y: int = 0,
    solver_name: str = "cadical195",
) -> CandidateResult:
    domain = dimensions(padding)
    cells = cap_cells(domain)
    with Solver(
        name=solver_name,
        bootstrap_with=instance_clauses(domain, phase_x, phase_y),
    ) as solver:
        baseline_sat = solver.solve()
        forced = 0
        first_failure = None
        for x, y in cells:
            expected = band_value(x, y, phase_x, phase_y)
            opposite = (
                domain.predecessor_var(x, y)
                if expected == 0
                else -domain.predecessor_var(x, y)
            )
            if solver.solve(assumptions=[opposite]):
                first_failure = (x, y)
                break
            forced += 1
        expanded_cells = [
            cell for cell in cells if cell[1] in (-1, domain.height)
        ]
        interior_cells = [
            cell for cell in cells if 0 <= cell[1] < domain.height
        ]
        expanded = (
            baseline_sat and bool(expanded_cells) and first_failure is None
        )
        interior = (
            baseline_sat and bool(interior_cells) and first_failure is None
        )
        return CandidateResult(
            padding=padding,
            phase=(phase_x, phase_y),
            output_size=(domain.width, domain.height),
            predecessor_size=(
                len(domain.predecessor_x),
                len(domain.predecessor_y),
            ),
            variables=domain.variables,
            clauses=clause_count(domain, phase_x, phase_y),
            baseline_sat=baseline_sat,
            queried_cells=len(cells),
            forced_cells=forced,
            expanded_rows_forced=expanded,
            canonical_interior_forced=interior,
            first_failure=first_failure,
            success=baseline_sat and bool(cells) and first_failure is None,
        )


def search(
    minimum: int,
    maximum: int,
    phase_x: int,
    phase_y: int,
    solver_name: str,
) -> dict:
    results = []
    for padding in range(minimum, maximum + 1):
        result = verify_candidate(padding, phase_x, phase_y, solver_name)
        results.append(result)
        if result.success:
            break
    return {
        "predicate": {
            "targets": "2p+8 by 2p+4 rectangular marching-band phase",
            "required_predecessor": (
                "matching g^2-fixed marching-band values on "
                "[10,2p-11] x [-1,2p+4]"
            ),
            "satisfiable": True,
            "universal": "each opposite queried bit is UNSAT",
        },
        "solver": solver_name,
        "range": [minimum, maximum],
        "results": [asdict(result) for result in results],
        "found": next(
            (asdict(result) for result in results if result.success), None
        ),
    }


def query_clauses(
    padding: int,
    phase_x: int,
    phase_y: int,
    cell: tuple[int, int],
) -> Iterator[list[int]]:
    domain = dimensions(padding)
    yield from instance_clauses(domain, phase_x, phase_y)
    x, y = cell
    expected = band_value(x, y, phase_x, phase_y)
    yield [
        domain.predecessor_var(x, y)
        if expected == 0
        else -domain.predecessor_var(x, y)
    ]


def mismatch_literal(
    domain: Domain, phase_x: int, phase_y: int, cell: tuple[int, int]
) -> int:
    x, y = cell
    expected = band_value(x, y, phase_x, phase_y)
    variable = domain.predecessor_var(x, y)
    return variable if expected == 0 else -variable


def forcing_claim_clauses(
    padding: int,
    phase_x: int,
    phase_y: int,
    cells: Sequence[tuple[int, int]],
) -> Iterator[list[int]]:
    yield from instance_clauses(dimensions(padding), phase_x, phase_y)
    yield [
        mismatch_literal(dimensions(padding), phase_x, phase_y, cell)
        for cell in cells
    ]


def model_bits(model: Sequence[int], variables: Iterable[int]) -> str:
    assignment = {abs(literal): literal > 0 for literal in model}
    return "".join("1" if assignment[variable] else "0" for variable in variables)


def witness_from_model(domain: Domain, model: Sequence[int]) -> dict:
    predecessor_rows = [
        model_bits(
            model,
            (domain.predecessor_var(x, y) for x in domain.predecessor_x),
        )
        for y in domain.predecessor_y
    ]
    middle_rows = [
        model_bits(model, (domain.middle_var(x, y) for x in domain.middle_x))
        for y in domain.middle_y
    ]
    return {"predecessor": predecessor_rows, "middle": middle_rows}


def replay_witness(
    domain: Domain,
    witness: dict,
    phase_x: int = 0,
    phase_y: int = 0,
) -> bool:
    predecessor = {
        (x, y): int(witness["predecessor"][row][column])
        for row, y in enumerate(domain.predecessor_y)
        for column, x in enumerate(domain.predecessor_x)
    }
    middle = {
        (x, y): int(witness["middle"][row][column])
        for row, y in enumerate(domain.middle_y)
        for column, x in enumerate(domain.middle_x)
    }
    for x, y in itertools.product(domain.middle_x, domain.middle_y):
        neighbors = [
            predecessor[x + dx, y + dy]
            for dx, dy in OFFSETS
            if (dx, dy) != (0, 0)
        ]
        if life(predecessor[x, y], neighbors) != middle[x, y]:
            return False
    for x, y in itertools.product(range(domain.width), range(domain.height)):
        neighbors = [
            middle[x + dx, y + dy]
            for dx, dy in OFFSETS
            if (dx, dy) != (0, 0)
        ]
        if life(middle[x, y], neighbors) != band_value(
            x, y, phase_x, phase_y
        ):
            return False
    return True


def predecessor_witness_bit(domain: Domain, witness: dict, x: int, y: int) -> int:
    return int(
        witness["predecessor"][y - domain.predecessor_y.start][
            x - domain.predecessor_x.start
        ]
    )


def analyze_slice(
    padding: int,
    row: int,
    phase_x: int,
    phase_y: int,
    solver_name: str,
) -> dict:
    domain = dimensions(padding)
    results = []
    forced_cells = []
    with Solver(
        name=solver_name,
        bootstrap_with=instance_clauses(domain, phase_x, phase_y),
    ) as solver:
        if not solver.solve():
            raise RuntimeError("the base cap instance is UNSAT")
        baseline = witness_from_model(domain, solver.get_model())
        if not replay_witness(domain, baseline, phase_x, phase_y):
            raise RuntimeError("the baseline SAT model does not replay")
        for x in domain.predecessor_x:
            cell = (x, row)
            mismatch = mismatch_literal(domain, phase_x, phase_y, cell)
            if solver.solve(assumptions=[mismatch]):
                witness = witness_from_model(domain, solver.get_model())
                if not replay_witness(domain, witness, phase_x, phase_y):
                    raise RuntimeError(f"SAT model for {cell} does not replay")
                expected = band_value(x, row, phase_x, phase_y)
                if predecessor_witness_bit(domain, witness, x, row) == expected:
                    raise RuntimeError(f"SAT model for {cell} does not differ")
                results.append(
                    {
                        "cell": cell,
                        "forced": False,
                        "expected": expected,
                        "witnessed": 1 - expected,
                        "witness": witness,
                    }
                )
            else:
                forced_cells.append(cell)
                results.append({"cell": cell, "forced": True})
    return {
        "padding": padding,
        "phase": [phase_x, phase_y],
        "row": row,
        "output_size": [domain.width, domain.height],
        "baseline_witness": baseline,
        "forced_cells": forced_cells,
        "results": results,
    }


def write_dimacs(
    path: Path,
    padding: int,
    phase_x: int,
    phase_y: int,
    cell: tuple[int, int],
) -> dict:
    domain = dimensions(padding)
    count = sum(1 for _ in query_clauses(padding, phase_x, phase_y, cell))
    digest = hashlib.sha256()
    with path.open("wb") as output:
        header = f"p cnf {domain.variables} {count}\n".encode()
        output.write(header)
        digest.update(header)
        for clause in query_clauses(padding, phase_x, phase_y, cell):
            line = (" ".join(map(str, clause)) + " 0\n").encode()
            output.write(line)
            digest.update(line)
    return {
        "path": str(path),
        "variables": domain.variables,
        "clauses": count,
        "sha256": digest.hexdigest(),
        "interpretation": "UNSAT iff the selected predecessor cell is forced",
    }


def write_forcing_claim_dimacs(
    path: Path,
    padding: int,
    phase_x: int,
    phase_y: int,
    cells: Sequence[tuple[int, int]],
) -> dict:
    domain = dimensions(padding)
    clauses = forcing_claim_clauses(
        padding, phase_x, phase_y, tuple(cells)
    )
    count = clause_count(domain, phase_x, phase_y) + 1
    digest = hashlib.sha256()
    with path.open("wb") as output:
        header = f"p cnf {domain.variables} {count}\n".encode()
        output.write(header)
        digest.update(header)
        for clause in clauses:
            line = (" ".join(map(str, clause)) + " 0\n").encode()
            output.write(line)
            digest.update(line)
    return {
        "path": str(path),
        "variables": domain.variables,
        "clauses": count,
        "sha256": digest.hexdigest(),
        "claimed_cells": [list(cell) for cell in cells],
        "interpretation": (
            "UNSAT iff every listed predecessor cell has its marching-band value"
        ),
    }


def independently_check_unsat(path: Path, solver_name: str) -> bool:
    formula = CNF(from_file=str(path))
    with Solver(name=solver_name, bootstrap_with=formula.clauses) as solver:
        return not solver.solve()


def parse_pair(value: str) -> tuple[int, int]:
    parts = value.split(",")
    if len(parts) != 2:
        raise argparse.ArgumentTypeError("expected X,Y")
    return int(parts[0]), int(parts[1])


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--min-padding", type=int, default=14)
    parser.add_argument("--max-padding", type=int, default=20)
    parser.add_argument("--phase", type=parse_pair, default=(0, 0))
    parser.add_argument("--solver", default="cadical195")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--emit-query", type=Path)
    parser.add_argument("--emit-forcing-claim", type=Path)
    parser.add_argument("--analyze-slice", type=int)
    parser.add_argument("--check-solver", default="glucose42")
    parser.add_argument("--padding", type=int, default=20)
    parser.add_argument("--cell", type=parse_pair, default=(10, -1))
    args = parser.parse_args()

    if args.analyze_slice is not None:
        report = analyze_slice(
            args.padding,
            args.analyze_slice,
            *args.phase,
            args.solver,
        )
        if args.emit_forcing_claim:
            slice_cells = [tuple(cell) for cell in report["forced_cells"]]
            candidate_cells = list(cap_cells(dimensions(args.padding)))
            claim_cells = list(dict.fromkeys(candidate_cells + slice_cells))
            certificate = write_forcing_claim_dimacs(
                args.emit_forcing_claim,
                args.padding,
                *args.phase,
                claim_cells,
            )
            certificate["claims"] = {
                "cap_transition": [list(cell) for cell in candidate_cells],
                "transverse_slice": [list(cell) for cell in slice_cells],
            }
            certificate["check_solver"] = args.check_solver
            certificate["checked_unsat"] = independently_check_unsat(
                args.emit_forcing_claim, args.check_solver
            )
            if not certificate["checked_unsat"]:
                raise RuntimeError("exported forcing claim is not UNSAT")
            report["certificate"] = certificate
    elif args.emit_forcing_claim:
        raise SystemExit("--emit-forcing-claim requires --analyze-slice")
    elif args.emit_query:
        report = write_dimacs(
            args.emit_query, args.padding, *args.phase, args.cell
        )
    else:
        report = search(
            args.min_padding,
            args.max_padding,
            *args.phase,
            args.solver,
        )
    rendered = json.dumps(report, indent=2)
    if args.output:
        args.output.write_text(rendered + "\n")
    print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
