from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from math import lcm

from .pattern import PeriodicPattern, Window
from .period3_transfer import REPRESENTATIVES as PERIOD3_REPRESENTATIVES
from .verify import verify_cells

MARGIN = 4
PUMP_OFFSET = 2
LIFT_PERIOD = lcm(1, 2, 3, 4)

# The other nonempty orbits are the five period-3 orbits, the 4x4 block
# agar, and alternating rows (all covered by earlier constructive theorems).
REPRESENTATIVES = (
    ("....", "..11", "..11"),
    ("...1", "..1.", "..11"),
    ("....", "...1", "1.1.", "...1"),
    ("...1", "..1.", ".1..", "1..."),
    ("..11", "11..", "..11", "11.."),
)

KNOWN_REPRESENTATIVES = (
    ((".",), "empty"),
    *[(rows, f"period3-{index}") for index, rows in enumerate(PERIOD3_REPRESENTATIVES)],
    (("11..", "11..", "....", "...."), "separated-block"),
    (("1111", "....", "1111", "...."), "alternating-rows"),
    *[(rows, f"new-{index}") for index, rows in enumerate(REPRESENTATIVES)],
)


def _lift(rows: tuple[str, ...]) -> tuple[str, ...]:
    height = len(rows)
    width = len(rows[0])
    return tuple(
        "".join(rows[y % height][x % width] for x in range(LIFT_PERIOD))
        for y in range(LIFT_PERIOD)
    )


def _transform(x: int, y: int, index: int) -> tuple[int, int]:
    return (
        (x, y),
        (-y, x),
        (-x, -y),
        (y, -x),
        (-x, y),
        (x, -y),
        (y, x),
        (-y, -x),
    )[index]


def _orbit(rows: tuple[str, ...]) -> set[tuple[str, ...]]:
    live = {
        (x, y)
        for y, row in enumerate(_lift(rows))
        for x, cell in enumerate(row)
        if cell == "1"
    }
    result = set()
    for transform in range(8):
        image = {
            tuple(coordinate % LIFT_PERIOD for coordinate in _transform(x, y, transform))
            for x, y in live
        }
        for dx in range(LIFT_PERIOD):
            for dy in range(LIFT_PERIOD):
                result.add(
                    tuple(
                        "".join(
                            "1"
                            if ((x - dx) % LIFT_PERIOD, (y - dy) % LIFT_PERIOD)
                            in image
                            else "."
                            for x in range(LIFT_PERIOD)
                        )
                        for y in range(LIFT_PERIOD)
                    )
                )
    return result


def classify_periods_at_most_4() -> dict[str, object]:
    stable_by_period: dict[str, int] = {}
    stable_lifts = set()
    for height in range(1, 5):
        for width in range(1, 5):
            count = 0
            for bits in range(1 << (width * height)):
                rows = tuple(
                    "".join(
                        "1" if bits & (1 << (width * y + x)) else "."
                        for x in range(width)
                    )
                    for y in range(height)
                )
                if not PeriodicPattern(rows).validate_still_life():
                    count += 1
                    stable_lifts.add(_lift(rows))
            stable_by_period[f"{width}x{height}"] = count

    orbits = {name: _orbit(rows) & stable_lifts for rows, name in KNOWN_REPRESENTATIVES}
    covered = set().union(*orbits.values())
    overlap_count = sum(map(len, orbits.values())) - len(covered)
    return {
        "candidate_tile_count": sum(
            1 << (width * height)
            for width in range(1, 5)
            for height in range(1, 5)
        ),
        "stable_tile_counts": stable_by_period,
        "distinct_lifted_hosts": len(stable_lifts),
        "symmetry_orbit_count": len(orbits),
        "orbit_sizes": {name: len(hosts) for name, hosts in orbits.items()},
        "covered_host_count": len(covered),
        "uncovered_host_count": len(stable_lifts - covered),
        "orbit_overlap_count": overlap_count,
    }


def pump_length_x(representative: int) -> int:
    return 2 * len(REPRESENTATIVES[representative][0])


def pump_length_y(representative: int) -> int:
    return 2 * len(REPRESENTATIVES[representative])


def threshold_x(representative: int) -> int:
    return PUMP_OFFSET + pump_length_x(representative)


def threshold_y(representative: int) -> int:
    return PUMP_OFFSET + pump_length_y(representative)


@dataclass(frozen=True)
class Period4Seed:
    representative: int
    window: Window
    live_cells: frozenset[tuple[int, int]]
    horizontal_pump: bool
    vertical_pump: bool

    @property
    def pattern(self) -> PeriodicPattern:
        return PeriodicPattern(
            REPRESENTATIVES[self.representative],
            f"bounded-period-representative-{self.representative}",
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
    def from_dict(cls, data: dict[str, object]) -> "Period4Seed":
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
    for representative, rows in enumerate(REPRESENTATIVES):
        period_x = len(rows[0])
        period_y = len(rows)
        x_threshold = threshold_x(representative)
        y_threshold = threshold_y(representative)
        for y in range(period_y):
            for x in range(period_x):
                for height in range(1, y_threshold + pump_length_y(representative)):
                    for width in range(1, x_threshold + pump_length_x(representative)):
                        yield (
                            representative,
                            Window(x, y, width, height),
                            width >= x_threshold,
                            height >= y_threshold,
                        )


def _equal_columns(seed: Period4Seed, first: int, second: int) -> bool:
    ymin = seed.window.y - MARGIN
    ymax = seed.window.y + seed.window.height - 1 + MARGIN
    return all(
        ((first, y) in seed.live_cells) == ((second, y) in seed.live_cells)
        for y in range(ymin, ymax + 1)
    )


def _equal_rows(seed: Period4Seed, first: int, second: int) -> bool:
    xmin = seed.window.x - MARGIN
    xmax = seed.window.x + seed.window.width - 1 + MARGIN
    return all(
        ((x, first) in seed.live_cells) == ((x, second) in seed.live_cells)
        for x in range(xmin, xmax + 1)
    )


def verify_seed(seed: Period4Seed) -> list[str]:
    errors = verify_cells(seed.pattern, seed.window, MARGIN, set(seed.live_cells))
    if seed.horizontal_pump:
        start = seed.window.x + PUMP_OFFSET
        cut = start + pump_length_x(seed.representative)
        for offset in (-2, -1):
            if not _equal_columns(seed, start + offset, cut + offset):
                errors.append(f"horizontal seam context {offset} does not match")
    if seed.vertical_pump:
        start = seed.window.y + PUMP_OFFSET
        cut = start + pump_length_y(seed.representative)
        for offset in (-2, -1):
            if not _equal_rows(seed, start + offset, cut + offset):
                errors.append(f"vertical seam context {offset} does not match")
    return errors


def pump_horizontal(seed: Period4Seed, copies: int = 1) -> Period4Seed:
    if not seed.horizontal_pump:
        raise ValueError("seed has no horizontal pump")
    result = seed
    length = pump_length_x(seed.representative)
    for _ in range(copies):
        start = result.window.x + PUMP_OFFSET
        cut = start + length
        shifted = {
            (x + length if x >= cut else x, y) for x, y in result.live_cells
        }
        inserted = {
            (x + length, y)
            for x, y in result.live_cells
            if start <= x < cut
        }
        result = Period4Seed(
            result.representative,
            Window(
                result.window.x,
                result.window.y,
                result.window.width + length,
                result.window.height,
            ),
            frozenset(shifted | inserted),
            True,
            result.vertical_pump,
        )
    return result


def pump_vertical(seed: Period4Seed, copies: int = 1) -> Period4Seed:
    if not seed.vertical_pump:
        raise ValueError("seed has no vertical pump")
    result = seed
    length = pump_length_y(seed.representative)
    for _ in range(copies):
        start = result.window.y + PUMP_OFFSET
        cut = start + length
        shifted = {
            (x, y + length if y >= cut else y) for x, y in result.live_cells
        }
        inserted = {
            (x, y + length)
            for x, y in result.live_cells
            if start <= y < cut
        }
        result = Period4Seed(
            result.representative,
            Window(
                result.window.x,
                result.window.y,
                result.window.width,
                result.window.height + length,
            ),
            frozenset(shifted | inserted),
            result.horizontal_pump,
            True,
        )
    return result


def construct_from_seeds(
    representative: int,
    window: Window,
    seeds: dict[tuple[int, int, int, int, int], Period4Seed],
) -> set[tuple[int, int]]:
    rows = REPRESENTATIVES[representative]
    x_threshold = threshold_x(representative)
    y_threshold = threshold_y(representative)
    x_length = pump_length_x(representative)
    y_length = pump_length_y(representative)
    base_width = (
        window.width
        if window.width < x_threshold
        else x_threshold + (window.width - x_threshold) % x_length
    )
    base_height = (
        window.height
        if window.height < y_threshold
        else y_threshold + (window.height - y_threshold) % y_length
    )
    seed = seeds[
        (
            representative,
            window.x % len(rows[0]),
            window.y % len(rows),
            base_width,
            base_height,
        )
    ]
    if window.width >= x_threshold:
        seed = pump_horizontal(seed, (window.width - base_width) // x_length)
    if window.height >= y_threshold:
        seed = pump_vertical(seed, (window.height - base_height) // y_length)
    dx = window.x - seed.window.x
    dy = window.y - seed.window.y
    return {(x + dx, y + dy) for x, y in seed.live_cells}


def verify_period4_certificate(certificate: object) -> list[str]:
    if not isinstance(certificate, dict):
        return ["certificate must be an object"]
    if certificate.get("format") != "periods-at-most-4-pump-certificate-v1":
        return ["unrecognized certificate format"]
    if certificate.get("theorem") != (
        "every rectangular window of every Life still life with horizontal and "
        "vertical periods at most 4 has a finite still-life extension with "
        "margin at most 4"
    ):
        return ["theorem statement does not match"]
    classification = classify_periods_at_most_4()
    if certificate.get("classification") != classification:
        return ["bounded-period tile classification does not match"]
    if (
        classification["distinct_lifted_hosts"] != 251
        or classification["symmetry_orbit_count"] != 13
        or classification["covered_host_count"] != 251
        or classification["uncovered_host_count"] != 0
        or classification["orbit_overlap_count"] != 0
    ):
        return ["internal bounded-period classification theorem failed"]
    raw_seeds = certificate.get("seeds")
    if not isinstance(raw_seeds, list):
        return ["seeds must be an array"]
    payload = json.dumps(raw_seeds, sort_keys=True, separators=(",", ":"))
    if certificate.get("seed_sha256") != hashlib.sha256(payload.encode()).hexdigest():
        return ["seed digest does not match"]
    try:
        seeds = [Period4Seed.from_dict(data) for data in raw_seeds]
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
        "seed_count": len(expected_specs),
        "new_representative_count": len(REPRESENTATIVES),
        "classified_orbit_count": len(KNOWN_REPRESENTATIVES),
        "margin_bound": MARGIN,
        "pump_offset": PUMP_OFFSET,
    }
    if certificate.get("summary") != expected_summary:
        errors.append("summary does not match")
    return errors
