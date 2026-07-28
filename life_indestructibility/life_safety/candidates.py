from dataclasses import dataclass

from .gliders import (
    CollisionResult,
    check_all_single_gliders,
    enumerate_interacting_attacks,
    simulate_collision,
)
from .life import Pattern


def _transform(cell: tuple[int, int], transform: int) -> tuple[int, int]:
    x, y = cell
    return (
        (x, y),
        (-y, x),
        (-x, -y),
        (y, -x),
        (-x, y),
        (x, -y),
        (y, x),
        (-y, -x),
    )[transform]


def canonical_pattern(pattern: Pattern) -> tuple[tuple[int, int], ...]:
    variants: list[tuple[tuple[int, int], ...]] = []
    for transform in range(8):
        transformed = [_transform(cell, transform) for cell in pattern]
        min_x = min(x for x, _ in transformed)
        min_y = min(y for _, y in transformed)
        variants.append(
            tuple(sorted((x - min_x, y - min_y) for x, y in transformed))
        )
    return min(variants)


@dataclass(frozen=True)
class StillLifeClass:
    identifier: str
    pattern: Pattern


@dataclass(frozen=True)
class CandidateResult:
    candidate: StillLifeClass
    collisions: tuple[CollisionResult, ...]
    exclusion_witness: CollisionResult | None

    @property
    def restored(self) -> int:
        return sum(result.outcome == "restored" for result in self.collisions)

    @property
    def settled_changed(self) -> int:
        return sum(
            result.outcome == "changed_periodic" for result in self.collisions
        )

    @property
    def unresolved(self) -> int:
        return sum(
            result.outcome == "unresolved_by_horizon"
            for result in self.collisions
        )


@dataclass(frozen=True)
class CandidateExclusion:
    candidate: StillLifeClass
    attack_count: int
    attacks_tried: int
    witness: CollisionResult | None


def _stable_row(
    above: int,
    current: int,
    below: int,
    expected: int,
    width: int,
) -> bool:
    for x in range(-1, width + 1):
        neighbors = sum(
            bool(row & (1 << neighbor_x))
            for row in (above, current, below)
            for neighbor_x in (x - 1, x, x + 1)
            if 0 <= neighbor_x < width
        )
        alive = 0 <= x < width and bool(current & (1 << x))
        neighbors -= alive
        output = neighbors == 3 or (alive and neighbors == 2)
        expected_alive = 0 <= x < width and bool(expected & (1 << x))
        if output != expected_alive:
            return False
    return True


def _enumerate_still_lives(width: int, height: int) -> tuple[Pattern, ...]:
    row_count = 1 << width
    transitions = {
        (above, current): tuple(
            below
            for below in range(row_count)
            if _stable_row(above, current, below, current, width)
        )
        for above in range(row_count)
        for current in range(row_count)
    }
    rows: list[tuple[int, ...]] = []

    def extend(prefix: tuple[int, ...]) -> None:
        if len(prefix) == height:
            if _stable_row(prefix[-2], prefix[-1], 0, prefix[-1], width) and (
                _stable_row(prefix[-1], 0, 0, 0, width)
            ):
                rows.append(prefix)
            return
        above = prefix[-2] if len(prefix) > 1 else 0
        for below in transitions[above, prefix[-1]]:
            extend(prefix + (below,))

    for first in range(row_count):
        if _stable_row(0, 0, first, 0, width):
            extend((first,))
    return tuple(
        frozenset(
            (x, y)
            for y, row in enumerate(pattern_rows)
            for x in range(width)
            if row & (1 << x)
        )
        for pattern_rows in rows
    )


def enumerate_still_life_classes(
    width: int = 4, height: int = 4
) -> tuple[StillLifeClass, ...]:
    if width < 2 or height < 2:
        raise ValueError("dimensions must be at least two")
    classes = {
        canonical_pattern(pattern)
        for pattern in _enumerate_still_lives(width, height)
        if pattern
    }
    ordered = sorted(classes, key=lambda pattern: (len(pattern), pattern))
    return tuple(
        StillLifeClass(
            f"sl{width}x{height}_{index:03d}",
            frozenset(pattern),
        )
        for index, pattern in enumerate(ordered)
    )


def search_still_life_classes(
    width: int = 4,
    height: int = 4,
    collision_horizon: int = 256,
) -> tuple[CandidateResult, ...]:
    output: list[CandidateResult] = []
    for candidate in enumerate_still_life_classes(width, height):
        collisions = check_all_single_gliders(
            candidate.pattern, collision_horizon=collision_horizon
        )
        witness = next(
            (
                collision
                for collision in collisions
                if collision.outcome == "changed_periodic"
            ),
            None,
        )
        output.append(CandidateResult(candidate, collisions, witness))
    return tuple(output)


def exclude_still_life_classes(
    width: int = 5,
    height: int = 5,
    collision_horizon: int = 512,
) -> tuple[CandidateExclusion, ...]:
    output: list[CandidateExclusion] = []
    for candidate in enumerate_still_life_classes(width, height):
        attacks = enumerate_interacting_attacks(candidate.pattern)
        witness = None
        attacks_tried = 0
        for attack in attacks:
            attacks_tried += 1
            collision = simulate_collision(
                candidate.pattern,
                attack,
                horizon=collision_horizon,
                keep_trace=0,
            )
            if collision.outcome == "changed_periodic":
                witness = collision
                break
        output.append(
            CandidateExclusion(
                candidate,
                len(attacks),
                attacks_tried,
                witness,
            )
        )
    return tuple(output)
