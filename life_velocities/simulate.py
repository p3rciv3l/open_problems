from __future__ import annotations

from typing import Any

from .model import SearchSpec
from .quotient import StripQuotient


def _next(alive: bool, neighbors: int) -> bool:
    return neighbors == 3 or (alive and neighbors == 2)


def verify_witness(witness: dict[str, Any]) -> list[str]:
    """Independently check a serialized witness, including every seam crossing."""
    if witness.get("status") != "sat":
        return ["result is not a SAT witness"]
    spec = SearchSpec(**witness["spec"])
    quotient = StripQuotient(
        spec.period,
        spec.displacement,
        spec.length,
        spec.width,
        spec.seam_phase,
    )
    live = {tuple(value) for value in witness["live_cosets"]}
    live_background = {tuple(value) for value in witness["live_background"]}

    def cell(t: int, x: int, y: int) -> bool:
        return quotient.key(t, x, y) in live

    def background(t: int, x: int, y: int) -> bool:
        return (
            t % spec.background_period,
            x % spec.background_x_period,
            y % spec.background_y_period,
        ) in live_background

    errors: list[str] = []
    # Multiple translated fundamental rectangles deliberately exercise both
    # longitudinal seams rather than trusting the SAT variable enumeration.
    for t in range(-spec.period, 2 * spec.period):
        for x in range(-spec.length, 2 * spec.length):
            for y in range(-1, spec.width + 1):
                count = sum(
                    cell(t, x + dx, y + dy)
                    for dy in (-1, 0, 1)
                    for dx in (-1, 0, 1)
                    if (dx, dy) != (0, 0)
                )
                if cell(t + 1, x, y) != _next(cell(t, x, y), count):
                    errors.append(f"Life mismatch at {(t, x, y)}")
                    return errors

    for t in range(-spec.period, spec.period + 1):
        for x in range(-spec.length, spec.length + 1):
            for y in range(spec.width):
                if cell(t + spec.period, x + spec.displacement, y) != cell(t, x, y):
                    errors.append(f"translation mismatch at {(t, x, y)}")
                    return errors
                if cell(t - spec.seam_phase, x + spec.length, y) != cell(t, x, y):
                    errors.append(f"spatial seam mismatch at {(t, x, y)}")
                    return errors

    if spec.require_motion and all(
        cell(spec.period, x, y) == cell(0, x, y)
        for x in range(spec.length)
        for y in range(spec.width)
    ):
        errors.append("witness is stationary over the required period")
        return errors

    for t in range(-spec.background_period, 2 * spec.background_period):
        for x in range(-spec.background_x_period, 2 * spec.background_x_period):
            for y in range(-spec.background_y_period, 2 * spec.background_y_period):
                count = sum(
                    background(t, x + dx, y + dy)
                    for dy in (-1, 0, 1)
                    for dx in (-1, 0, 1)
                    if (dx, dy) != (0, 0)
                )
                if background(t + 1, x, y) != _next(background(t, x, y), count):
                    errors.append(f"background Life mismatch at {(t, x, y)}")
                    return errors

    guard_x = list(range(spec.guard_columns)) + list(
        range(spec.length - spec.guard_columns, spec.length)
    )
    for t in range(spec.period):
        for x in guard_x:
            for y in range(spec.width):
                if cell(t, x, y) != background(t + spec.background_phase, x, y):
                    errors.append(f"background guard mismatch at {(t, x, y)}")
                    return errors

    differs = any(
        cell(t, x, y) != background(t + spec.background_phase, x, y)
        for t in range(spec.period)
        for x in range(spec.guard_columns, spec.length - spec.guard_columns)
        for y in range(spec.width)
    )
    if not differs:
        errors.append("witness has no interior departure from background")
    if spec.require_live_background and not live_background:
        errors.append("witness background is empty")
    return errors
