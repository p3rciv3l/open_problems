from dataclasses import dataclass

from .gliders import CollisionResult, check_all_single_gliders
from .life import Pattern, bounding_box, step


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


def enumerate_still_life_classes(
    width: int = 4, height: int = 4
) -> tuple[StillLifeClass, ...]:
    if width < 1 or height < 1:
        raise ValueError("dimensions must be positive")
    cells = tuple((x, y) for y in range(height) for x in range(width))
    classes: set[tuple[tuple[int, int], ...]] = set()
    for mask in range(1, 1 << len(cells)):
        pattern = frozenset(
            cell for index, cell in enumerate(cells) if mask & (1 << index)
        )
        xmin, _, ymin, _ = bounding_box(pattern)
        if xmin != 0 or ymin != 0 or step(pattern) != pattern:
            continue
        classes.add(canonical_pattern(pattern))
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
