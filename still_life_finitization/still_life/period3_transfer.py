from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

from .pattern import PeriodicPattern, Window
from .verify import verify_cells

MARGIN = 4
PUMP_THRESHOLD = 10
PUMP_LENGTH = 6
PUMP_OFFSET = 2
REPRESENTATIVES = (
    ("11.", "1..", "1.."),
    ("11.", "11.", "..."),
    ("11.", "1..", ".1."),
    ("11.", "1..", "..1"),
    ("1..", "1..", ".11"),
)


def _transforms(x: int, y: int) -> tuple[tuple[int, int], ...]:
    return (
        (x, y),
        (-y, x),
        (-x, -y),
        (y, -x),
        (-x, y),
        (x, -y),
        (y, x),
        (-y, -x),
    )


def canonical_period3(rows: tuple[str, str, str]) -> tuple[str, str, str]:
    live = {(x, y) for y in range(3) for x in range(3) if rows[y][x] == "1"}
    images = []
    for transform in range(8):
        transformed = {_transforms(x, y)[transform] for x, y in live}
        for dx in range(3):
            for dy in range(3):
                image = {
                    ((x + dx) % 3, (y + dy) % 3) for x, y in transformed
                }
                images.append(
                    tuple(
                        "".join("1" if (x, y) in image else "." for x in range(3))
                        for y in range(3)
                    )
                )
    return min(images)


def classify_period3_tiles() -> dict[str, object]:
    stable = []
    for bits in range(1 << 9):
        rows = tuple(
            "".join("1" if bits & (1 << (3 * y + x)) else "." for x in range(3))
            for y in range(3)
        )
        if not PeriodicPattern(rows).validate_still_life():
            stable.append(rows)
    nonempty = [rows for rows in stable if any("1" in row for row in rows)]
    return {
        "tile_count": 512,
        "stable_count": len(stable),
        "empty_count": sum(not any("1" in row for row in rows) for rows in stable),
        "four_live_count": sum(
            sum(row.count("1") for row in rows) == 4 for rows in stable
        ),
        "other_live_count": sum(
            sum(row.count("1") for row in rows) not in (0, 4) for rows in stable
        ),
        "symmetry_orbits": [
            list(rows) for rows in sorted({canonical_period3(rows) for rows in nonempty})
        ],
    }


@dataclass(frozen=True)
class Period3Seed:
    representative: int
    window: Window
    live_cells: frozenset[tuple[int, int]]
    horizontal_pump: bool
    vertical_pump: bool

    @property
    def pattern(self) -> PeriodicPattern:
        return PeriodicPattern(
            REPRESENTATIVES[self.representative],
            f"period-3-representative-{self.representative}",
        )

    def to_dict(self) -> dict[str, object]:
        xmin, ymin, xmax, ymax = self.window.expand(MARGIN)
        return {
            "representative": self.representative,
            "window": self.window.to_dict(),
            "horizontal_pump": self.horizontal_pump,
            "vertical_pump": self.vertical_pump,
            "rows": [
                "".join(
                    "1" if (x, y) in self.live_cells else "."
                    for x in range(xmin, xmax + 1)
                )
                for y in range(ymin, ymax + 1)
            ],
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "Period3Seed":
        representative = int(data["representative"])
        window = Window.from_dict(data["window"])
        xmin, ymin, xmax, ymax = window.expand(MARGIN)
        rows = data["rows"]
        if (
            not isinstance(rows, list)
            or len(rows) != ymax - ymin + 1
            or any(
                not isinstance(row, str)
                or len(row) != xmax - xmin + 1
                or any(cell not in ".1" for cell in row)
                for row in rows
            )
        ):
            raise ValueError("seed bitmap dimensions or alphabet are invalid")
        live_cells = frozenset(
            (xmin + x, ymin + y)
            for y, row in enumerate(rows)
            for x, cell in enumerate(row)
            if cell == "1"
        )
        return cls(
            representative,
            window,
            live_cells,
            bool(data["horizontal_pump"]),
            bool(data["vertical_pump"]),
        )


def seed_specs():
    for representative in range(len(REPRESENTATIVES)):
        for y in range(3):
            for x in range(3):
                for height in range(1, PUMP_THRESHOLD + PUMP_LENGTH):
                    for width in range(1, PUMP_THRESHOLD + PUMP_LENGTH):
                        yield (
                            representative,
                            Window(x, y, width, height),
                            width >= PUMP_THRESHOLD,
                            height >= PUMP_THRESHOLD,
                        )


def _equal_columns(seed: Period3Seed, first: int, second: int) -> bool:
    ymin = seed.window.y - MARGIN
    ymax = seed.window.y + seed.window.height - 1 + MARGIN
    return all(
        ((first, y) in seed.live_cells) == ((second, y) in seed.live_cells)
        for y in range(ymin, ymax + 1)
    )


def _equal_rows(seed: Period3Seed, first: int, second: int) -> bool:
    xmin = seed.window.x - MARGIN
    xmax = seed.window.x + seed.window.width - 1 + MARGIN
    return all(
        ((x, first) in seed.live_cells) == ((x, second) in seed.live_cells)
        for x in range(xmin, xmax + 1)
    )


def verify_seed(seed: Period3Seed) -> list[str]:
    errors = verify_cells(seed.pattern, seed.window, MARGIN, set(seed.live_cells))
    if seed.horizontal_pump:
        start = seed.window.x + PUMP_OFFSET
        cut = start + PUMP_LENGTH
        if not _equal_columns(seed, start - 2, cut - 2):
            errors.append("first horizontal seam context does not match")
        if not _equal_columns(seed, start - 1, cut - 1):
            errors.append("second horizontal seam context does not match")
    if seed.vertical_pump:
        start = seed.window.y + PUMP_OFFSET
        cut = start + PUMP_LENGTH
        if not _equal_rows(seed, start - 2, cut - 2):
            errors.append("first vertical seam context does not match")
        if not _equal_rows(seed, start - 1, cut - 1):
            errors.append("second vertical seam context does not match")
    return errors


def pump_horizontal(seed: Period3Seed, copies: int = 1) -> Period3Seed:
    if not seed.horizontal_pump:
        raise ValueError("seed has no horizontal pump")
    result = seed
    for _ in range(copies):
        start = result.window.x + PUMP_OFFSET
        cut = start + PUMP_LENGTH
        shifted = {
            (x + PUMP_LENGTH if x >= cut else x, y)
            for x, y in result.live_cells
        }
        inserted = {
            (x + PUMP_LENGTH, y)
            for x, y in result.live_cells
            if start <= x < cut
        }
        result = Period3Seed(
            result.representative,
            Window(
                result.window.x,
                result.window.y,
                result.window.width + PUMP_LENGTH,
                result.window.height,
            ),
            frozenset(shifted | inserted),
            True,
            result.vertical_pump,
        )
    return result


def pump_vertical(seed: Period3Seed, copies: int = 1) -> Period3Seed:
    if not seed.vertical_pump:
        raise ValueError("seed has no vertical pump")
    result = seed
    for _ in range(copies):
        start = result.window.y + PUMP_OFFSET
        cut = start + PUMP_LENGTH
        shifted = {
            (x, y + PUMP_LENGTH if y >= cut else y)
            for x, y in result.live_cells
        }
        inserted = {
            (x, y + PUMP_LENGTH)
            for x, y in result.live_cells
            if start <= y < cut
        }
        result = Period3Seed(
            result.representative,
            Window(
                result.window.x,
                result.window.y,
                result.window.width,
                result.window.height + PUMP_LENGTH,
            ),
            frozenset(shifted | inserted),
            result.horizontal_pump,
            True,
        )
    return result


def construct_from_seeds(
    representative: int,
    window: Window,
    seeds: dict[tuple[int, int, int, int, int], Period3Seed],
) -> set[tuple[int, int]]:
    base_width = (
        window.width
        if window.width < PUMP_THRESHOLD
        else PUMP_THRESHOLD + (window.width - PUMP_THRESHOLD) % PUMP_LENGTH
    )
    base_height = (
        window.height
        if window.height < PUMP_THRESHOLD
        else PUMP_THRESHOLD + (window.height - PUMP_THRESHOLD) % PUMP_LENGTH
    )
    seed = seeds[
        (
            representative,
            window.x % 3,
            window.y % 3,
            base_width,
            base_height,
        )
    ]
    if window.width >= PUMP_THRESHOLD:
        seed = pump_horizontal(seed, (window.width - base_width) // PUMP_LENGTH)
    if window.height >= PUMP_THRESHOLD:
        seed = pump_vertical(seed, (window.height - base_height) // PUMP_LENGTH)
    dx = window.x - seed.window.x
    dy = window.y - seed.window.y
    return {(x + dx, y + dy) for x, y in seed.live_cells}


def verify_period3_certificate(certificate: object) -> list[str]:
    if not isinstance(certificate, dict):
        return ["certificate must be an object"]
    if certificate.get("format") != "period-3-pump-certificate-v1":
        return ["unrecognized certificate format"]
    if certificate.get("theorem") != (
        "every rectangular window of every 3-by-3-periodic Life still life "
        "has a finite still-life extension with margin at most 4"
    ):
        return ["theorem statement does not match"]
    classification = classify_period3_tiles()
    if certificate.get("classification") != classification:
        return ["period-3 tile classification does not match"]
    if classification != {
        "tile_count": 512,
        "stable_count": 127,
        "empty_count": 1,
        "four_live_count": 126,
        "other_live_count": 0,
        "symmetry_orbits": [
            list(rows)
            for rows in sorted(
                {
                    canonical_period3(representative)
                    for representative in REPRESENTATIVES
                }
            )
        ],
    }:
        return ["internal period-3 classification theorem failed"]
    raw_seeds = certificate.get("seeds")
    if not isinstance(raw_seeds, list):
        return ["seeds must be an array"]
    payload = json.dumps(raw_seeds, sort_keys=True, separators=(",", ":"))
    if certificate.get("seed_sha256") != hashlib.sha256(payload.encode()).hexdigest():
        return ["seed digest does not match"]
    try:
        seeds = [Period3Seed.from_dict(data) for data in raw_seeds]
    except (IndexError, KeyError, TypeError, ValueError) as error:
        return [f"malformed seed: {error}"]
    expected_specs = list(seed_specs())
    actual_specs = [
        (
            seed.representative,
            seed.window,
            seed.horizontal_pump,
            seed.vertical_pump,
        )
        for seed in seeds
    ]
    if actual_specs != expected_specs:
        return ["seed coverage or ordering does not match"]
    errors = []
    for index, seed in enumerate(seeds):
        errors.extend(f"seed {index}: {error}" for error in verify_seed(seed))
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
            first = pump_vertical(pump_horizontal(seed))
            second = pump_horizontal(pump_vertical(seed))
            if first != second:
                errors.append(f"seed {index}: pumps do not commute")
            errors.extend(
                f"seed {index} combined pump: {error}" for error in verify_seed(first)
            )
    expected_summary = {
        "seed_count": 10125,
        "representative_count": 5,
        "phase_count": 9,
        "margin_bound": MARGIN,
        "pump_threshold": PUMP_THRESHOLD,
        "pump_length": PUMP_LENGTH,
    }
    if certificate.get("summary") != expected_summary:
        errors.append("summary does not match")
    return errors
