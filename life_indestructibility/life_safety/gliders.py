from dataclasses import dataclass

from .life import (
    Cell,
    Pattern,
    bounding_box,
    evolve,
    serialize,
    step,
    translate,
)

DIRECTIONS: dict[str, Cell] = {
    "SE": (1, 1),
    "SW": (-1, 1),
    "NW": (-1, -1),
    "NE": (1, -1),
}
BASE_GLIDER: Pattern = frozenset({(1, 0), (2, 1), (0, 2), (1, 2), (2, 2)})


def _rotate(cell: Cell, direction: str) -> Cell:
    x, y = cell
    return {
        "SE": (x, y),
        "SW": (-x, y),
        "NW": (-x, -y),
        "NE": (x, -y),
    }[direction]


def glider(direction: str, phase: int) -> Pattern:
    if direction not in DIRECTIONS:
        raise ValueError(f"unknown direction: {direction}")
    if phase not in range(4):
        raise ValueError("phase must be 0, 1, 2, or 3")
    pattern = frozenset(_rotate(cell, direction) for cell in BASE_GLIDER)
    return evolve(pattern, phase)[-1]


def lane_of_translation(direction: str, translation: Cell) -> int:
    dx, dy = DIRECTIONS[direction]
    tx, ty = translation
    return dx * ty - dy * tx


def _translation_for_lane(direction: str, lane: int) -> Cell:
    dx, dy = DIRECTIONS[direction]
    return (0, lane // dx) if dx else (-lane // dy, 0)


def _touches(a: Pattern, b: Pattern) -> bool:
    return any(
        abs(ax - bx) <= 1 and abs(ay - by) <= 1
        for ax, ay in a
        for bx, by in b
    )


@dataclass(frozen=True)
class Attack:
    direction: str
    phase: int
    lane: int
    initial_glider: Pattern


@dataclass(frozen=True)
class CollisionResult:
    attack: Attack
    restored_generation: int | None
    settled_generation: int | None
    settled_period: int | None
    final: Pattern
    trace: tuple[Pattern, ...]

    @property
    def certified_restored(self) -> bool:
        return self.restored_generation is not None

    @property
    def outcome(self) -> str:
        if self.certified_restored:
            return "restored"
        if self.settled_generation is not None:
            return "changed_periodic"
        return "unresolved_by_horizon"

    def as_dict(self) -> dict[str, object]:
        return {
            "direction": self.attack.direction,
            "phase": self.attack.phase,
            "lane": self.attack.lane,
            "initial_glider": serialize(self.attack.initial_glider),
            "certified_restored": self.certified_restored,
            "restored_generation": self.restored_generation,
            "outcome": self.outcome,
            "settled_generation": self.settled_generation,
            "settled_period": self.settled_period,
            "final": serialize(self.final),
            "trace": [serialize(pattern) for pattern in self.trace],
        }


def enumerate_interacting_attacks(
    target: Pattern, approach_margin: int = 6
) -> tuple[Attack, ...]:
    """Enumerate all direction/phase/lane classes geometrically hitting target.

    The target must be a nonempty still life. A lane is included exactly when
    the isolated glider's Moore neighborhood touches the target. Translation
    along the direction is normalized to one upstream starting position. Each
    glider is evolved until its directional bounding-box edge has passed the
    target, so the search has no target-size-dependent timeout.
    """
    if not target:
        raise ValueError("target must be nonempty")
    if step(target) != target:
        raise ValueError("exhaustive finite lane enumeration requires a still life")
    xmin, xmax, _, _ = bounding_box(target)
    attacks: list[Attack] = []
    for direction, (dx, dy) in DIRECTIONS.items():
        for phase in range(4):
            shape = glider(direction, phase)
            cross_values = [dx * y - dy * x for x, y in target]
            shape_cross = [dx * y - dy * x for x, y in shape]
            lane_min = min(cross_values) - max(shape_cross) - 2
            lane_max = max(cross_values) - min(shape_cross) + 2
            for lane in range(lane_min, lane_max + 1):
                tx, ty = _translation_for_lane(direction, lane)
                candidate = translate(shape, tx, ty)
                while not (
                    (dx > 0 and max(x for x, _ in candidate) < xmin - approach_margin)
                    or (dx < 0 and min(x for x, _ in candidate) > xmax + approach_margin)
                ):
                    candidate = translate(candidate, -4 * dx, -4 * dy)
                trajectory = candidate
                interacts = False
                while True:
                    if _touches(trajectory, target):
                        interacts = True
                        break
                    trajectory = step(trajectory)
                    bx0, bx1, _, _ = bounding_box(trajectory)
                    if (
                        (dx > 0 and bx0 > xmax + 1)
                        or (dx < 0 and bx1 < xmin - 1)
                    ):
                        break
                if interacts:
                    attacks.append(Attack(direction, phase, lane, candidate))
    return tuple(attacks)


def simulate_collision(
    target: Pattern, attack: Attack, horizon: int = 128, keep_trace: int = 16
) -> CollisionResult:
    current = frozenset(target | attack.initial_glider)
    trace = [current]
    touched = False
    restored = None
    settled_generation = None
    settled_period = None
    seen: dict[Pattern, int] = {}
    for generation in range(1, horizon + 1):
        touched = touched or _touches(current - target, target)
        current = step(current)
        if len(trace) < keep_trace:
            trace.append(current)
        if touched and current == target:
            restored = generation
            break
        if touched:
            if current in seen:
                settled_generation = generation
                settled_period = generation - seen[current]
                break
            seen[current] = generation
    return CollisionResult(
        attack,
        restored,
        settled_generation,
        settled_period,
        current,
        tuple(trace),
    )


def check_all_single_gliders(
    target: Pattern, collision_horizon: int = 128
) -> tuple[CollisionResult, ...]:
    return tuple(
        simulate_collision(target, attack, collision_horizon)
        for attack in enumerate_interacting_attacks(target)
    )
