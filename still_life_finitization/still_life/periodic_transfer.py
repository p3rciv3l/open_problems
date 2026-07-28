from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping

from .pattern import PeriodicPattern, Window
from .verify import verify_cells

SeedKey = tuple[int, int, int, int]


@dataclass(frozen=True)
class PumpParameters:
    margin: int
    horizontal_length: int
    vertical_length: int
    horizontal_offset: int
    vertical_offset: int
    horizontal_threshold: int
    vertical_threshold: int

    def validate(self, pattern: PeriodicPattern) -> list[str]:
        errors = []
        if self.margin < 0:
            errors.append("margin must be nonnegative")
        if self.horizontal_length <= 0:
            errors.append("horizontal pump length must be positive")
        elif self.horizontal_length % pattern.width:
            errors.append("horizontal pump length must be a host-period multiple")
        if self.vertical_length <= 0:
            errors.append("vertical pump length must be positive")
        elif self.vertical_length % pattern.height:
            errors.append("vertical pump length must be a host-period multiple")
        if self.horizontal_offset < 2:
            errors.append("horizontal pump offset must be at least two")
        if self.vertical_offset < 2:
            errors.append("vertical pump offset must be at least two")
        if (
            self.horizontal_threshold
            < self.horizontal_offset + self.horizontal_length
        ):
            errors.append("horizontal threshold does not contain the pump block")
        if self.vertical_threshold < self.vertical_offset + self.vertical_length:
            errors.append("vertical threshold does not contain the pump block")
        return errors


@dataclass(frozen=True)
class PeriodicPumpSeed:
    window: Window
    live_cells: frozenset[tuple[int, int]]


def seed_key(pattern: PeriodicPattern, window: Window) -> SeedKey:
    return (
        window.x % pattern.width,
        window.y % pattern.height,
        window.width,
        window.height,
    )


def base_dimension(size: int, threshold: int, pump_length: int) -> int:
    if size < threshold:
        return size
    return threshold + (size - threshold) % pump_length


def required_seed_windows(
    pattern: PeriodicPattern, parameters: PumpParameters
) -> Iterable[Window]:
    max_width = parameters.horizontal_threshold + parameters.horizontal_length
    max_height = parameters.vertical_threshold + parameters.vertical_length
    for y in range(pattern.height):
        for x in range(pattern.width):
            for height in range(1, max_height):
                for width in range(1, max_width):
                    yield Window(x, y, width, height)


def _equal_columns(
    seed: PeriodicPumpSeed, margin: int, first: int, second: int
) -> bool:
    ymin = seed.window.y - margin
    ymax = seed.window.y + seed.window.height - 1 + margin
    return all(
        ((first, y) in seed.live_cells) == ((second, y) in seed.live_cells)
        for y in range(ymin, ymax + 1)
    )


def _equal_rows(
    seed: PeriodicPumpSeed, margin: int, first: int, second: int
) -> bool:
    xmin = seed.window.x - margin
    xmax = seed.window.x + seed.window.width - 1 + margin
    return all(
        ((x, first) in seed.live_cells) == ((x, second) in seed.live_cells)
        for x in range(xmin, xmax + 1)
    )


def verify_seed(
    pattern: PeriodicPattern,
    parameters: PumpParameters,
    seed: PeriodicPumpSeed,
) -> list[str]:
    errors = verify_cells(
        pattern, seed.window, parameters.margin, set(seed.live_cells)
    )
    if seed.window.width >= parameters.horizontal_threshold:
        start = seed.window.x + parameters.horizontal_offset
        cut = start + parameters.horizontal_length
        for context in (-2, -1):
            if not _equal_columns(
                seed, parameters.margin, start + context, cut + context
            ):
                errors.append(f"horizontal seam context {context} does not match")
    if seed.window.height >= parameters.vertical_threshold:
        start = seed.window.y + parameters.vertical_offset
        cut = start + parameters.vertical_length
        for context in (-2, -1):
            if not _equal_rows(
                seed, parameters.margin, start + context, cut + context
            ):
                errors.append(f"vertical seam context {context} does not match")
    return errors


def pump_horizontal(
    seed: PeriodicPumpSeed, parameters: PumpParameters, copies: int = 1
) -> PeriodicPumpSeed:
    if copies < 0:
        raise ValueError("copies must be nonnegative")
    if seed.window.width < parameters.horizontal_threshold:
        raise ValueError("seed is below the horizontal pump threshold")
    result = seed
    length = parameters.horizontal_length
    for _ in range(copies):
        start = result.window.x + parameters.horizontal_offset
        cut = start + length
        shifted = {
            (x + length if x >= cut else x, y) for x, y in result.live_cells
        }
        inserted = {
            (x + length, y)
            for x, y in result.live_cells
            if start <= x < cut
        }
        result = PeriodicPumpSeed(
            Window(
                result.window.x,
                result.window.y,
                result.window.width + length,
                result.window.height,
            ),
            frozenset(shifted | inserted),
        )
    return result


def pump_vertical(
    seed: PeriodicPumpSeed, parameters: PumpParameters, copies: int = 1
) -> PeriodicPumpSeed:
    if copies < 0:
        raise ValueError("copies must be nonnegative")
    if seed.window.height < parameters.vertical_threshold:
        raise ValueError("seed is below the vertical pump threshold")
    result = seed
    length = parameters.vertical_length
    for _ in range(copies):
        start = result.window.y + parameters.vertical_offset
        cut = start + length
        shifted = {
            (x, y + length if y >= cut else y) for x, y in result.live_cells
        }
        inserted = {
            (x, y + length)
            for x, y in result.live_cells
            if start <= y < cut
        }
        result = PeriodicPumpSeed(
            Window(
                result.window.x,
                result.window.y,
                result.window.width,
                result.window.height + length,
            ),
            frozenset(shifted | inserted),
        )
    return result


def verify_seed_table(
    pattern: PeriodicPattern,
    parameters: PumpParameters,
    seeds: Mapping[SeedKey, PeriodicPumpSeed],
) -> list[str]:
    errors = pattern.validate_still_life() + parameters.validate(pattern)
    if errors:
        return errors
    required = {
        seed_key(pattern, window): window
        for window in required_seed_windows(pattern, parameters)
    }
    missing = required.keys() - seeds.keys()
    extra = seeds.keys() - required.keys()
    if missing:
        errors.append(f"seed table is missing {len(missing)} keys")
    if extra:
        errors.append(f"seed table has {len(extra)} unexpected keys")
    for key in required.keys() & seeds.keys():
        seed = seeds[key]
        if seed_key(pattern, seed.window) != key:
            errors.append(f"seed {key} has the wrong window key")
            continue
        seed_errors = verify_seed(pattern, parameters, seed)
        errors.extend(f"seed {key}: {error}" for error in seed_errors)
    return errors


def construct_from_seeds(
    pattern: PeriodicPattern,
    parameters: PumpParameters,
    seeds: Mapping[SeedKey, PeriodicPumpSeed],
    window: Window,
) -> set[tuple[int, int]]:
    base_width = base_dimension(
        window.width,
        parameters.horizontal_threshold,
        parameters.horizontal_length,
    )
    base_height = base_dimension(
        window.height,
        parameters.vertical_threshold,
        parameters.vertical_length,
    )
    key = (
        window.x % pattern.width,
        window.y % pattern.height,
        base_width,
        base_height,
    )
    seed = seeds[key]
    horizontal_copies = (
        (window.width - base_width) // parameters.horizontal_length
    )
    vertical_copies = (window.height - base_height) // parameters.vertical_length
    if horizontal_copies:
        seed = pump_horizontal(seed, parameters, horizontal_copies)
    if vertical_copies:
        seed = pump_vertical(seed, parameters, vertical_copies)
    dx = window.x - seed.window.x
    dy = window.y - seed.window.y
    return {(x + dx, y + dy) for x, y in seed.live_cells}
