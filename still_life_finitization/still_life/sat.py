from __future__ import annotations

import hashlib
import itertools
import time
from dataclasses import dataclass

from pysat.formula import CNF
from pysat.solvers import Solver

from .pattern import PeriodicPattern, Window
from .verify import verify_cells


@dataclass
class Encoding:
    cnf: CNF
    variables: dict[tuple[int, int], int]
    bounds: tuple[int, int, int, int]

    def digest(self) -> str:
        payload = "\n".join(" ".join(map(str, clause)) + " 0" for clause in self.cnf.clauses)
        return hashlib.sha256(payload.encode()).hexdigest()


def _forbid_assignment(variables: list[int], values: tuple[bool, ...]) -> list[int]:
    return [-variable if value else variable for variable, value in zip(variables, values)]


def build_encoding(pattern: PeriodicPattern, window: Window, margin: int) -> Encoding:
    xmin, ymin, xmax, ymax = window.expand(margin)
    coordinates = [
        (x, y)
        for y in range(ymin, ymax + 1)
        for x in range(xmin, xmax + 1)
    ]
    variables = {cell: index + 1 for index, cell in enumerate(coordinates)}
    cnf = CNF()

    for x, y in window.cells():
        variable = variables[(x, y)]
        cnf.append([variable if pattern.alive(x, y) else -variable])

    for y in range(ymin - 1, ymax + 2):
        for x in range(xmin - 1, xmax + 2):
            center = variables.get((x, y))
            neighbors = [
                variables[(x + dx, y + dy)]
                for dy in (-1, 0, 1)
                for dx in (-1, 0, 1)
                if (dx, dy) != (0, 0) and (x + dx, y + dy) in variables
            ]
            local_variables = ([center] if center is not None else []) + neighbors
            for values in itertools.product((False, True), repeat=len(local_variables)):
                center_alive = values[0] if center is not None else False
                neighbor_values = values[1:] if center is not None else values
                count = sum(neighbor_values)
                invalid = (center_alive and count not in (2, 3)) or (
                    not center_alive and count == 3
                )
                if invalid:
                    cnf.append(_forbid_assignment(local_variables, values))

    return Encoding(cnf, variables, (xmin, ymin, xmax, ymax))


def solve_margin(
    pattern: PeriodicPattern,
    window: Window,
    margin: int,
    solver_name: str = "cadical195",
) -> tuple[dict[str, object], dict[str, object] | None]:
    encoding = build_encoding(pattern, window, margin)
    started = time.perf_counter()
    with Solver(name=solver_name, bootstrap_with=encoding.cnf) as solver:
        satisfiable = solver.solve()
        elapsed = time.perf_counter() - started
        stats = solver.accum_stats()
        model = solver.get_model() if satisfiable else None

    outcome: dict[str, object] = {
        "margin": margin,
        "status": "SAT" if satisfiable else "UNSAT",
        "variables": len(encoding.variables),
        "clauses": len(encoding.cnf.clauses),
        "cnf_sha256": encoding.digest(),
        "solver": solver_name,
        "solver_stats": stats,
        "elapsed_seconds": elapsed,
    }
    if not satisfiable:
        return outcome, None

    positive = {literal for literal in model if literal > 0}
    live_cells = {
        cell for cell, variable in encoding.variables.items() if variable in positive
    }
    errors = verify_cells(pattern, window, margin, live_cells)
    if errors:
        raise RuntimeError("SAT model failed independent verification: " + "; ".join(errors[:5]))
    witness: dict[str, object] = {
        "format": "still-life-finitization-witness-v1",
        "pattern": pattern.to_dict(),
        "window": window.to_dict(),
        "margin": margin,
        "bounds": list(encoding.bounds),
        "live_cells": [list(cell) for cell in sorted(live_cells, key=lambda p: (p[1], p[0]))],
        "verification": "passed",
    }
    return outcome, witness


def enumerate_margins(
    pattern: PeriodicPattern,
    window: Window,
    max_margin: int,
    solver_name: str = "cadical195",
) -> dict[str, object]:
    if max_margin < 0:
        raise ValueError("max_margin must be nonnegative")
    pattern_errors = pattern.validate_still_life()
    if pattern_errors:
        raise ValueError("tile is not a periodic still life: " + "; ".join(pattern_errors[:5]))

    outcomes = []
    witness = None
    for margin in range(max_margin + 1):
        outcome, witness = solve_margin(pattern, window, margin, solver_name)
        outcomes.append(outcome)
        if witness is not None:
            break

    result: dict[str, object] = {
        "format": "still-life-finitization-result-v1",
        "pattern": pattern.to_dict(),
        "window": window.to_dict(),
        "searched_through": outcomes[-1]["margin"],
        "outcomes": outcomes,
        "minimum_margin": witness["margin"] if witness else None,
        "lower_bound": witness["margin"] if witness else max_margin + 1,
        "witness": witness,
    }
    return result
