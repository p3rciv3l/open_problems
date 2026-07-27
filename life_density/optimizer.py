"""Z3 encoding for exact bounded optimization under solver trust."""

from __future__ import annotations

import time
from typing import Any

import z3

from .verify import verify_result


def _proper_divisors(period: int) -> list[int]:
    return [d for d in range(1, period) if period % d == 0]


def _rows_from_model(
    model: z3.ModelRef,
    cells: list[list[list[z3.BoolRef]]],
    width: int,
    height: int,
    period: int,
) -> list[list[str]]:
    return [
        [
            "".join(
                "O" if z3.is_true(model.eval(cells[t][y][x], model_completion=True)) else "."
                for x in range(width)
            )
            for y in range(height)
        ]
        for t in range(period)
    ]


def _result_with_witness(
    *,
    status: str,
    width: int,
    height: int,
    period: int,
    exact_period: bool,
    seed: int,
    elapsed: float,
    total_live: int,
    phases: list[list[str]],
    bounds: dict[str, int] | None = None,
    reason_unknown: str | None = None,
) -> dict[str, Any]:
    spacetime_cells = width * height * period
    result: dict[str, Any] = {
        "schema": "life-density/v1",
        "status": status,
        "parameters": {
            "width": width,
            "height": height,
            "period": period,
            "exact_period": exact_period,
            "topology": "torus_directional_moore",
            "rule": "B3/S23",
        },
        "objective": {
            "total_live": total_live,
            "spacetime_cells": spacetime_cells,
            "density": {"numerator": total_live, "denominator": spacetime_cells},
            "density_decimal": format(total_live / spacetime_cells, ".12f"),
        },
        "witness": {"phases": phases},
        "solver": {
            "backend": "z3",
            "version": z3.get_version_string(),
            "seed": seed,
            "elapsed_seconds": round(elapsed, 6),
            "method": "incremental binary search over finite integer bounds",
        },
    }
    if bounds is not None:
        result["bounds"] = bounds
    if reason_unknown is not None:
        result["solver"]["reason_unknown"] = reason_unknown
    verification = verify_result(result)
    if not verification["valid"]:
        raise RuntimeError(f"internal witness verification failed: {verification['errors']}")
    result["verification"] = verification
    return result


def optimize(
    width: int,
    height: int,
    period: int,
    *,
    exact_period: bool = False,
    timeout_seconds: float | None = None,
    seed: int = 0,
) -> dict[str, Any]:
    """Find and prove the maximum spacetime population, or report unknown."""
    if any(isinstance(v, bool) or not isinstance(v, int) or v <= 0 for v in (width, height, period)):
        raise ValueError("width, height, and period must be positive integers")
    if timeout_seconds is not None and timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be positive")

    started = time.monotonic()
    cells = [
        [
            [z3.Bool(f"x_{t}_{y}_{x}") for x in range(width)]
            for y in range(height)
        ]
        for t in range(period)
    ]
    solver = z3.Solver()
    solver.set(random_seed=seed)

    for t in range(period):
        next_t = (t + 1) % period
        for y in range(height):
            for x in range(width):
                neighbor_count = z3.Sum(
                    [
                        z3.If(cells[t][(y + dy) % height][(x + dx) % width], 1, 0)
                        for dy in (-1, 0, 1)
                        for dx in (-1, 0, 1)
                        if dx != 0 or dy != 0
                    ]
                )
                survives = z3.And(
                    cells[t][y][x],
                    z3.Or(neighbor_count == 2, neighbor_count == 3),
                )
                born = z3.And(z3.Not(cells[t][y][x]), neighbor_count == 3)
                solver.add(cells[next_t][y][x] == z3.Or(survives, born))

    if exact_period:
        for divisor in _proper_divisors(period):
            solver.add(
                z3.Or(
                    [
                        cells[0][y][x] != cells[divisor][y][x]
                        for y in range(height)
                        for x in range(width)
                    ]
                )
            )

    population = z3.Sum(
        [z3.If(cells[t][y][x], 1, 0) for t in range(period) for y in range(height) for x in range(width)]
    )
    maximum = width * height * period

    def check_at_least(bound: int) -> tuple[z3.CheckSatResult, z3.ModelRef | None]:
        if timeout_seconds is not None:
            remaining_ms = int((timeout_seconds - (time.monotonic() - started)) * 1000)
            if remaining_ms <= 0:
                return z3.unknown, None
            solver.set(timeout=max(1, remaining_ms))
        solver.push()
        solver.add(population >= bound)
        outcome = solver.check()
        model = solver.model() if outcome == z3.sat else None
        solver.pop()
        return outcome, model

    outcome, best_model = check_at_least(0)
    if outcome == z3.unsat:
        return {
            "schema": "life-density/v1",
            "status": "unsat",
            "parameters": {
                "width": width,
                "height": height,
                "period": period,
                "exact_period": exact_period,
                "topology": "torus_directional_moore",
                "rule": "B3/S23",
            },
            "solver": {
                "backend": "z3",
                "version": z3.get_version_string(),
                "seed": seed,
                "elapsed_seconds": round(time.monotonic() - started, 6),
            },
        }
    if outcome == z3.unknown:
        return {
            "schema": "life-density/v1",
            "status": "unknown",
            "parameters": {
                "width": width,
                "height": height,
                "period": period,
                "exact_period": exact_period,
                "topology": "torus_directional_moore",
                "rule": "B3/S23",
            },
            "bounds": {"lower": 0, "upper": maximum},
            "solver": {
                "backend": "z3",
                "version": z3.get_version_string(),
                "seed": seed,
                "elapsed_seconds": round(time.monotonic() - started, 6),
                "reason_unknown": solver.reason_unknown(),
            },
        }

    lower, upper = 0, maximum
    while lower < upper:
        candidate = (lower + upper + 1) // 2
        outcome, model = check_at_least(candidate)
        if outcome == z3.sat:
            lower = candidate
            best_model = model
        elif outcome == z3.unsat:
            upper = candidate - 1
        else:
            phases = _rows_from_model(best_model, cells, width, height, period)
            actual = sum(row.count("O") for phase in phases for row in phase)
            return _result_with_witness(
                status="unknown",
                width=width,
                height=height,
                period=period,
                exact_period=exact_period,
                seed=seed,
                elapsed=time.monotonic() - started,
                total_live=actual,
                phases=phases,
                bounds={"lower": actual, "upper": upper},
                reason_unknown=solver.reason_unknown(),
            )

    assert best_model is not None
    phases = _rows_from_model(best_model, cells, width, height, period)
    actual = sum(row.count("O") for phase in phases for row in phase)
    if actual != lower:
        raise RuntimeError(f"solver model population {actual} differs from optimum {lower}")
    return _result_with_witness(
        status="optimal",
        width=width,
        height=height,
        period=period,
        exact_period=exact_period,
        seed=seed,
        elapsed=time.monotonic() - started,
        total_live=actual,
        phases=phases,
        bounds={"lower": lower, "upper": upper},
    )
