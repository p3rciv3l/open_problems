from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

from pysat.solvers import Solver

from .pattern import PeriodicPattern, Window
from .sat import build_encoding
from .verify import verify_cells

STRIPE_PATTERN = PeriodicPattern(("1", "."), "alternating-live-rows")
COLUMN_STRIPE_PATTERN = PeriodicPattern(("1.",), "alternating-live-columns")
MARGIN = 3
HORIZONTAL_START = 3
HORIZONTAL_LENGTH = 3
VERTICAL_OFFSET = 4
VERTICAL_LENGTH = 4


@dataclass(frozen=True)
class StripeSeed:
    window: Window
    live_cells: frozenset[tuple[int, int]]
    horizontal_pump: bool
    vertical_pump: bool

    def to_dict(self, encoding: dict[str, object]) -> dict[str, object]:
        return {
            "window": self.window.to_dict(),
            "margin": MARGIN,
            "horizontal_pump": self.horizontal_pump,
            "vertical_pump": self.vertical_pump,
            "live_cells": [
                list(cell)
                for cell in sorted(self.live_cells, key=lambda point: (point[1], point[0]))
            ],
            "encoding": encoding,
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "StripeSeed":
        return cls(
            Window.from_dict(data["window"]),
            frozenset(tuple(cell) for cell in data["live_cells"]),
            data["horizontal_pump"],
            data["vertical_pump"],
        )


def _add_equality(clauses, first: int, second: int) -> None:
    clauses.append([-first, second])
    clauses.append([first, -second])


def build_seed_encoding(
    window: Window,
    horizontal_pump: bool,
    vertical_pump: bool,
):
    encoding = build_encoding(STRIPE_PATTERN, window, MARGIN)
    if horizontal_pump:
        for y in range(window.y - MARGIN, window.y + window.height + MARGIN):
            _add_equality(
                encoding.cnf,
                encoding.variables[(HORIZONTAL_START - 2, y)],
                encoding.variables[
                    (HORIZONTAL_START + HORIZONTAL_LENGTH - 2, y)
                ],
            )
            _add_equality(
                encoding.cnf,
                encoding.variables[(HORIZONTAL_START - 1, y)],
                encoding.variables[
                    (HORIZONTAL_START + HORIZONTAL_LENGTH - 1, y)
                ],
            )
    if vertical_pump:
        start = window.y + VERTICAL_OFFSET
        for x in range(window.x - MARGIN, window.x + window.width + MARGIN):
            _add_equality(
                encoding.cnf,
                encoding.variables[(x, start - 2)],
                encoding.variables[(x, start + VERTICAL_LENGTH - 2)],
            )
            _add_equality(
                encoding.cnf,
                encoding.variables[(x, start - 1)],
                encoding.variables[(x, start + VERTICAL_LENGTH - 1)],
            )
    return encoding


def solve_seed(
    window: Window,
    horizontal_pump: bool,
    vertical_pump: bool,
    solver_name: str = "cadical195",
) -> tuple[StripeSeed, dict[str, object]]:
    encoding = build_seed_encoding(window, horizontal_pump, vertical_pump)
    with Solver(name=solver_name, bootstrap_with=encoding.cnf) as solver:
        if not solver.solve():
            raise RuntimeError(f"pump seed is UNSAT: {window}")
        model = {literal for literal in solver.get_model() if literal > 0}
        stats = solver.accum_stats()
    live_cells = frozenset(
        cell
        for cell, variable in encoding.variables.items()
        if variable in model
    )
    seed = StripeSeed(window, live_cells, horizontal_pump, vertical_pump)
    errors = verify_seed(seed)
    if errors:
        raise RuntimeError("; ".join(errors))
    metadata = {
        "variables": len(encoding.variables),
        "clauses": len(encoding.cnf.clauses),
        "cnf_sha256": encoding.digest(),
        "solver": solver_name,
        "solver_stats": stats,
    }
    return seed, metadata


def _equal_columns(seed: StripeSeed, first: int, second: int) -> bool:
    ymin = seed.window.y - MARGIN
    ymax = seed.window.y + seed.window.height - 1 + MARGIN
    return all(
        ((first, y) in seed.live_cells) == ((second, y) in seed.live_cells)
        for y in range(ymin, ymax + 1)
    )


def _equal_rows(seed: StripeSeed, first: int, second: int) -> bool:
    xmin = seed.window.x - MARGIN
    xmax = seed.window.x + seed.window.width - 1 + MARGIN
    return all(
        ((x, first) in seed.live_cells) == ((x, second) in seed.live_cells)
        for x in range(xmin, xmax + 1)
    )


def pump_horizontal(seed: StripeSeed, copies: int = 1) -> StripeSeed:
    if not seed.horizontal_pump:
        raise ValueError("seed has no horizontal pump")
    result = seed
    for _ in range(copies):
        start = HORIZONTAL_START
        cut = start + HORIZONTAL_LENGTH
        shifted = {
            (x + HORIZONTAL_LENGTH if x >= cut else x, y)
            for x, y in result.live_cells
        }
        inserted = {
            (x + HORIZONTAL_LENGTH, y)
            for x, y in result.live_cells
            if start <= x < cut
        }
        result = StripeSeed(
            Window(
                result.window.x,
                result.window.y,
                result.window.width + HORIZONTAL_LENGTH,
                result.window.height,
            ),
            frozenset(shifted | inserted),
            True,
            result.vertical_pump,
        )
    return result


def pump_vertical(seed: StripeSeed, copies: int = 1) -> StripeSeed:
    if not seed.vertical_pump:
        raise ValueError("seed has no vertical pump")
    result = seed
    for _ in range(copies):
        start = result.window.y + VERTICAL_OFFSET
        cut = start + VERTICAL_LENGTH
        shifted = {
            (x, y + VERTICAL_LENGTH if y >= cut else y)
            for x, y in result.live_cells
        }
        inserted = {
            (x, y + VERTICAL_LENGTH)
            for x, y in result.live_cells
            if start <= y < cut
        }
        result = StripeSeed(
            Window(
                result.window.x,
                result.window.y,
                result.window.width,
                result.window.height + VERTICAL_LENGTH,
            ),
            frozenset(shifted | inserted),
            result.horizontal_pump,
            True,
        )
    return result


def verify_seed(seed: StripeSeed) -> list[str]:
    errors = verify_cells(STRIPE_PATTERN, seed.window, MARGIN, set(seed.live_cells))
    if seed.horizontal_pump:
        start = HORIZONTAL_START
        cut = start + HORIZONTAL_LENGTH
        if not _equal_columns(seed, start - 2, cut - 2):
            errors.append("first horizontal seam context does not match")
        if not _equal_columns(seed, start - 1, cut - 1):
            errors.append("second horizontal seam context does not match")
    if seed.vertical_pump:
        start = seed.window.y + VERTICAL_OFFSET
        cut = start + VERTICAL_LENGTH
        if not _equal_rows(seed, start - 2, cut - 2):
            errors.append("first vertical seam context does not match")
        if not _equal_rows(seed, start - 1, cut - 1):
            errors.append("second vertical seam context does not match")
    return errors


def seed_specs():
    for phase in (0, 1):
        for width in range(1, 9):
            for height in range(1, 9):
                yield Window(0, phase, width, height), False, False
        for width in (9, 10, 11):
            for height in range(1, 9):
                yield Window(0, phase, width, height), True, False
        for width in range(1, 9):
            for height in (9, 10, 11, 12):
                yield Window(0, phase, width, height), False, True
        for width in (9, 10, 11):
            for height in (9, 10, 11, 12):
                yield Window(0, phase, width, height), True, True


def construct_from_seeds(
    window: Window, seeds: dict[tuple[int, int, int], StripeSeed]
) -> set[tuple[int, int]]:
    phase = window.y % 2
    base_width = window.width if window.width < 9 else 9 + (window.width - 9) % 3
    base_height = (
        window.height if window.height < 9 else 9 + (window.height - 9) % 4
    )
    seed = seeds[(phase, base_width, base_height)]
    if window.width >= 9:
        seed = pump_horizontal(seed, (window.width - base_width) // 3)
    if window.height >= 9:
        seed = pump_vertical(seed, (window.height - base_height) // 4)
    dy = window.y - seed.window.y
    dx = window.x
    return {(x + dx, y + dy) for x, y in seed.live_cells}


def construct_columns_from_seeds(
    window: Window, seeds: dict[tuple[int, int, int], StripeSeed]
) -> set[tuple[int, int]]:
    transposed = Window(window.y, window.x, window.height, window.width)
    return {(y, x) for x, y in construct_from_seeds(transposed, seeds)}


def verify_stripe_certificate(certificate: object) -> list[str]:
    if not isinstance(certificate, dict):
        return ["certificate must be an object"]
    if certificate.get("format") != "alternating-row-pump-certificate-v1":
        return ["unrecognized certificate format"]
    if certificate.get("theorem") != (
        "all finite rectangular windows have stabilization margin at most 3"
    ):
        return ["theorem statement does not match"]
    if certificate.get("pattern") != {
        "name": "alternating-live-rows",
        "rows": ["1", "."],
    }:
        return ["pattern does not match"]
    raw_seeds = certificate.get("seeds")
    if not isinstance(raw_seeds, list):
        return ["seeds must be an array"]
    payload = json.dumps(raw_seeds, sort_keys=True, separators=(",", ":"))
    if certificate.get("seed_sha256") != hashlib.sha256(payload.encode()).hexdigest():
        return ["seed digest does not match"]
    try:
        seeds = [StripeSeed.from_dict(data) for data in raw_seeds]
    except (KeyError, TypeError, ValueError) as error:
        return [f"malformed seed: {error}"]
    errors = []
    expected_specs = list(seed_specs())
    actual_specs = [
        (seed.window, seed.horizontal_pump, seed.vertical_pump) for seed in seeds
    ]
    if actual_specs != expected_specs:
        errors.append("seed coverage or ordering does not match the theorem partition")
    for index, (seed, raw_seed) in enumerate(zip(seeds, raw_seeds)):
        errors.extend(f"seed {index}: {error}" for error in verify_seed(seed))
        encoding = build_seed_encoding(
            seed.window, seed.horizontal_pump, seed.vertical_pump
        )
        raw_encoding = raw_seed.get("encoding")
        if not isinstance(raw_encoding, dict):
            errors.append(f"seed {index}: encoding metadata is missing")
        else:
            expected_encoding = {
                "variables": len(encoding.variables),
                "clauses": len(encoding.cnf.clauses),
                "cnf_sha256": encoding.digest(),
                "solver": "cadical195",
            }
            if any(
                raw_encoding.get(key) != value
                for key, value in expected_encoding.items()
            ):
                errors.append(f"seed {index}: encoding metadata does not match")
            if not isinstance(raw_encoding.get("solver_stats"), dict):
                errors.append(f"seed {index}: solver statistics are missing")
        if seed.horizontal_pump:
            errors.extend(
                f"seed {index} horizontal pump: {error}"
                for error in verify_seed(pump_horizontal(seed))
            )
        if seed.vertical_pump:
            errors.extend(
                f"seed {index} vertical pump: {error}"
                for error in verify_seed(pump_vertical(seed))
            )
        if seed.horizontal_pump and seed.vertical_pump:
            horizontal_then_vertical = pump_vertical(pump_horizontal(seed))
            vertical_then_horizontal = pump_horizontal(pump_vertical(seed))
            if horizontal_then_vertical != vertical_then_horizontal:
                errors.append(f"seed {index}: pumps do not commute")
            errors.extend(
                f"seed {index} combined pump: {error}"
                for error in verify_seed(horizontal_then_vertical)
            )
    expected_summary = {
        "seed_count": 264,
        "finite_seed_count": 128,
        "horizontal_seed_count": 48,
        "vertical_seed_count": 64,
        "two_dimensional_seed_count": 24,
        "margin_bound": MARGIN,
        "horizontal_pump_length": HORIZONTAL_LENGTH,
        "vertical_pump_length": VERTICAL_LENGTH,
    }
    if certificate.get("summary") != expected_summary:
        errors.append("summary does not match")
    return errors
