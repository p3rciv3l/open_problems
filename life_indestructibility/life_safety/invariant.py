from dataclasses import dataclass
from itertools import product

from .life import Cell, Pattern, serialize

REGION = tuple((x, y) for y in range(3) for x in range(3))
BOUNDARY = tuple(
    (x, y)
    for y in range(-1, 4)
    for x in range(-1, 4)
    if not (0 <= x < 3 and 0 <= y < 3)
)
PROTECTED_INDEX = REGION.index((1, 1))
REGION_INDEX = {cell: index for index, cell in enumerate(REGION)}
BOUNDARY_INDEX = {cell: index for index, cell in enumerate(BOUNDARY)}


def _neighbor_masks() -> tuple[tuple[int, ...], tuple[int, ...]]:
    region_masks: list[int] = []
    boundary_masks: list[int] = []
    for x, y in REGION:
        region_mask = 0
        boundary_mask = 0
        for dx, dy in product((-1, 0, 1), repeat=2):
            if (dx, dy) == (0, 0):
                continue
            neighbor = x + dx, y + dy
            if neighbor in REGION_INDEX:
                region_mask |= 1 << REGION_INDEX[neighbor]
            if neighbor in BOUNDARY_INDEX:
                boundary_mask |= 1 << BOUNDARY_INDEX[neighbor]
        region_masks.append(region_mask)
        boundary_masks.append(boundary_mask)
    return tuple(region_masks), tuple(boundary_masks)


REGION_NEIGHBORS, BOUNDARY_NEIGHBORS = _neighbor_masks()


def transition(region_state: int, boundary_state: int) -> int:
    successor = 0
    for index in range(len(REGION)):
        neighbors = (region_state & REGION_NEIGHBORS[index]).bit_count()
        neighbors += (boundary_state & BOUNDARY_NEIGHBORS[index]).bit_count()
        alive = bool(region_state & (1 << index))
        if neighbors == 3 or (alive and neighbors == 2):
            successor |= 1 << index
    return successor


def decode_region(state: int) -> Pattern:
    return frozenset(
        cell for index, cell in enumerate(REGION) if state & (1 << index)
    )


def decode_boundary(state: int) -> Pattern:
    return frozenset(
        cell for index, cell in enumerate(BOUNDARY) if state & (1 << index)
    )


@dataclass(frozen=True)
class Elimination:
    region_state: int
    round: int
    boundary_state: int
    successor: int

    def as_dict(self) -> dict[str, object]:
        return {
            "region_state": self.region_state,
            "region_live": serialize(decode_region(self.region_state)),
            "round": self.round,
            "boundary_state": self.boundary_state,
            "boundary_live": serialize(decode_boundary(self.boundary_state)),
            "successor": self.successor,
            "successor_live": serialize(decode_region(self.successor)),
        }


@dataclass(frozen=True)
class InvariantSearchResult:
    protected_value: bool
    eliminations: tuple[Elimination, ...]
    invariant_states: tuple[int, ...]

    @property
    def excluded(self) -> bool:
        return not self.invariant_states

    def as_dict(self) -> dict[str, object]:
        round_counts: dict[int, int] = {}
        for elimination in self.eliminations:
            round_counts[elimination.round] = round_counts.get(elimination.round, 0) + 1
        return {
            "abstraction": "exact 3x3 region with adversarially refreshed boundary",
            "protected": [1, 1],
            "protected_value": int(self.protected_value),
            "safe_states": 1 << (len(REGION) - 1),
            "boundary_assignments_per_step": 1 << len(BOUNDARY),
            "excluded": self.excluded,
            "elimination_round_counts": [
                round_counts[round_number] for round_number in sorted(round_counts)
            ],
            "remaining_invariant_states": list(self.invariant_states),
            "eliminations": [
                elimination.as_dict() for elimination in self.eliminations
            ],
        }


def search_three_by_three_invariant(
    protected_value: bool = True,
) -> InvariantSearchResult:
    candidates = {
        state
        for state in range(1 << len(REGION))
        if bool(state & (1 << PROTECTED_INDEX)) == protected_value
    }
    eliminations: list[Elimination] = []
    round_number = 0
    while candidates:
        removed: list[Elimination] = []
        for state in sorted(candidates):
            for boundary in range(1 << len(BOUNDARY)):
                successor = transition(state, boundary)
                if successor not in candidates:
                    removed.append(
                        Elimination(state, round_number, boundary, successor)
                    )
                    break
        if not removed:
            break
        candidates.difference_update(
            elimination.region_state for elimination in removed
        )
        eliminations.extend(removed)
        round_number += 1
    return InvariantSearchResult(
        protected_value,
        tuple(eliminations),
        tuple(sorted(candidates)),
    )


def verify_exclusion(result: InvariantSearchResult) -> bool:
    ranks = {
        elimination.region_state: elimination.round
        for elimination in result.eliminations
    }
    safe_states = {
        state
        for state in range(1 << len(REGION))
        if bool(state & (1 << PROTECTED_INDEX)) == result.protected_value
    }
    if set(ranks) | set(result.invariant_states) != safe_states:
        return False
    for elimination in result.eliminations:
        if transition(elimination.region_state, elimination.boundary_state) != (
            elimination.successor
        ):
            return False
        successor_rank = ranks.get(elimination.successor)
        successor_is_safe = (
            bool(elimination.successor & (1 << PROTECTED_INDEX))
            == result.protected_value
        )
        if successor_is_safe and (
            successor_rank is None or successor_rank >= elimination.round
        ):
            return False
    return True
