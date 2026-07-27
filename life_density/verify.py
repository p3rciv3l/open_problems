"""Pure-Python witness simulation and validation (independent of Z3)."""

from __future__ import annotations

from typing import Any


def _parse_phases(result: dict[str, Any]) -> tuple[list[list[list[bool]]], list[str]]:
    errors: list[str] = []
    params = result.get("parameters", {})
    width = params.get("width")
    height = params.get("height")
    period = params.get("period")
    raw_phases = result.get("witness", {}).get("phases")
    if not all(isinstance(v, int) and v > 0 for v in (width, height, period)):
        return [], ["parameters width, height, and period must be positive integers"]
    if not isinstance(raw_phases, list) or len(raw_phases) != period:
        return [], [f"witness must contain exactly {period} phases"]

    phases: list[list[list[bool]]] = []
    for t, raw_phase in enumerate(raw_phases):
        if not isinstance(raw_phase, list) or len(raw_phase) != height:
            errors.append(f"phase {t} must contain exactly {height} rows")
            continue
        phase: list[list[bool]] = []
        for y, row in enumerate(raw_phase):
            if not isinstance(row, str) or len(row) != width:
                errors.append(f"phase {t} row {y} must be a string of length {width}")
                continue
            invalid = sorted(set(row) - {".", "O"})
            if invalid:
                errors.append(f"phase {t} row {y} has invalid characters: {invalid}")
            phase.append([cell == "O" for cell in row])
        if len(phase) == height:
            phases.append(phase)
    return phases, errors


def step(phase: list[list[bool]]) -> list[list[bool]]:
    """Apply B3/S23 with all eight wrapped directional offsets counted."""
    height = len(phase)
    width = len(phase[0])
    next_phase = [[False] * width for _ in range(height)]
    for y in range(height):
        for x in range(width):
            neighbors = sum(
                phase[(y + dy) % height][(x + dx) % width]
                for dy in (-1, 0, 1)
                for dx in (-1, 0, 1)
                if dx != 0 or dy != 0
            )
            next_phase[y][x] = neighbors == 3 or (phase[y][x] and neighbors == 2)
    return next_phase


def least_temporal_period(phases: list[list[list[bool]]]) -> int:
    period = len(phases)
    for divisor in range(1, period + 1):
        if period % divisor == 0 and all(
            phases[t] == phases[(t + divisor) % period] for t in range(period)
        ):
            return divisor
    raise AssertionError("the full sequence is always a period")


def verify_result(result: dict[str, Any]) -> dict[str, Any]:
    """Validate shape, every transition, objective, and exact-period claim."""
    errors: list[str] = []
    if result.get("schema") != "life-density/v1":
        errors.append("unsupported or missing schema")
    if result.get("status") not in {"optimal", "feasible", "unknown"}:
        errors.append("result has no verifiable witness status")

    phases, parse_errors = _parse_phases(result)
    errors.extend(parse_errors)
    if errors or not phases:
        return {"valid": False, "errors": errors, "least_period": None}

    for t, phase in enumerate(phases):
        if step(phase) != phases[(t + 1) % len(phases)]:
            errors.append(f"invalid Life transition from phase {t}")

    total_live = sum(cell for phase in phases for row in phase for cell in row)
    objective = result.get("objective", {})
    expected_cells = (
        result["parameters"]["width"]
        * result["parameters"]["height"]
        * result["parameters"]["period"]
    )
    if objective.get("total_live") != total_live:
        errors.append(
            f"objective total_live is {objective.get('total_live')}, expected {total_live}"
        )
    if objective.get("spacetime_cells") != expected_cells:
        errors.append("objective spacetime_cells is inconsistent with parameters")
    fraction = objective.get("density", {})
    if fraction.get("numerator") != total_live or fraction.get("denominator") != expected_cells:
        errors.append("objective density fraction is inconsistent with witness")

    least_period = least_temporal_period(phases)
    if result["parameters"].get("exact_period") and least_period != len(phases):
        errors.append(
            f"exact period requested but witness has temporal period {least_period}"
        )
    return {"valid": not errors, "errors": errors, "least_period": least_period}

