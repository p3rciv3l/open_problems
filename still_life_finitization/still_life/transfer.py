from __future__ import annotations

import hashlib
import itertools
import json
from dataclasses import dataclass

from .pattern import PeriodicPattern, Window
from .verify import verify_cells

Cell = tuple[int, int]
State = tuple[int, int, int, int]


def _finite_still_life_errors(live_cells: set[Cell]) -> list[str]:
    if not live_cells:
        return ["motif must contain a live cell"]
    errors = []
    xmin = min(x for x, _ in live_cells) - 1
    xmax = max(x for x, _ in live_cells) + 1
    ymin = min(y for _, y in live_cells) - 1
    ymax = max(y for _, y in live_cells) + 1
    for y in range(ymin, ymax + 1):
        for x in range(xmin, xmax + 1):
            count = sum(
                (x + dx, y + dy) in live_cells
                for dy in (-1, 0, 1)
                for dx in (-1, 0, 1)
                if (dx, dy) != (0, 0)
            )
            if (x, y) in live_cells and count not in (2, 3):
                errors.append(f"live ({x},{y}) has {count} neighbors")
            elif (x, y) not in live_cells and count == 3:
                errors.append(f"dead ({x},{y}) would be born")
    return errors


@dataclass(frozen=True)
class ComponentAgar:
    motif: frozenset[Cell]
    period_x: int
    period_y: int
    name: str

    def __post_init__(self) -> None:
        if self.period_x <= 0 or self.period_y <= 0:
            raise ValueError("periods must be positive")
        if not self.motif:
            raise ValueError("motif must be nonempty")
        if any(
            not (0 <= x < self.period_x and 0 <= y < self.period_y)
            for x, y in self.motif
        ):
            raise ValueError("motif cells must lie in the fundamental tile")

    @property
    def diameter(self) -> int:
        return max(
            max(abs(x1 - x2), abs(y1 - y2))
            for (x1, y1), (x2, y2) in itertools.product(self.motif, repeat=2)
        )

    def pattern(self) -> PeriodicPattern:
        rows = tuple(
            "".join(
                "1" if (x, y) in self.motif else "." for x in range(self.period_x)
            )
            for y in range(self.period_y)
        )
        return PeriodicPattern(rows, self.name)

    def copy_separation(self) -> int:
        distances = []
        for tx, ty in itertools.product((-1, 0, 1), repeat=2):
            if (tx, ty) == (0, 0):
                continue
            shifted = {
                (x + tx * self.period_x, y + ty * self.period_y)
                for x, y in self.motif
            }
            distances.append(
                min(
                    max(abs(x1 - x2), abs(y1 - y2))
                    for x1, y1 in self.motif
                    for x2, y2 in shifted
                )
            )
        return min(distances)

    def validate_components(self) -> list[str]:
        errors = _finite_still_life_errors(set(self.motif))
        separation = self.copy_separation()
        if separation < 3:
            errors.append(f"translated motifs have Chebyshev separation {separation}, below 3")
        return errors

    def complete_window(self, window: Window) -> set[Cell]:
        copies = set()
        motif_by_phase = {(x, y) for x, y in self.motif}
        for x, y in window.cells():
            phase = (x % self.period_x, y % self.period_y)
            if phase in motif_by_phase:
                copies.add((x - phase[0], y - phase[1]))
        return {
            (base_x + x, base_y + y)
            for base_x, base_y in copies
            for x, y in self.motif
        }

    def verify_window(self, window: Window) -> list[str]:
        return verify_cells(
            self.pattern(), window, self.diameter, self.complete_window(window)
        )


@dataclass(frozen=True)
class RectangleTransferAutomaton:
    period_x: int
    period_y: int

    def states(self):
        return itertools.product(
            range(self.period_x),
            range(self.period_x),
            range(self.period_y),
            range(self.period_y),
        )

    def initial_states(self):
        for x in range(self.period_x):
            for y in range(self.period_y):
                yield (x, x, y, y)

    def state(self, window: Window) -> State:
        return (
            window.x % self.period_x,
            (window.x + window.width - 1) % self.period_x,
            window.y % self.period_y,
            (window.y + window.height - 1) % self.period_y,
        )

    def transition(self, state: State, symbol: str) -> State:
        left, right, top, bottom = state
        if symbol == "E":
            return (left, (right + 1) % self.period_x, top, bottom)
        if symbol == "S":
            return (left, right, top, (bottom + 1) % self.period_y)
        raise ValueError(f"unknown transfer symbol: {symbol}")

    def canonical_window(self, state: State) -> Window:
        left, right, top, bottom = state
        width = (right - left) % self.period_x + 1
        height = (bottom - top) % self.period_y + 1
        return Window(left, top, width, height)


def analyze_component_agar(agar: ComponentAgar) -> dict[str, object]:
    component_errors = agar.validate_components()
    if component_errors:
        raise ValueError("; ".join(component_errors))
    pattern_errors = agar.pattern().validate_still_life()
    if pattern_errors:
        raise ValueError("; ".join(pattern_errors))

    automaton = RectangleTransferAutomaton(agar.period_x, agar.period_y)
    states = list(automaton.states())
    state_set = set(states)
    transitions = []
    canonical_errors = []
    for state in states:
        for symbol in ("E", "S"):
            target = automaton.transition(state, symbol)
            if target not in state_set:
                raise AssertionError("transfer escaped the finite state set")
            transitions.append([list(state), symbol, list(target)])
        if automaton.transition(automaton.transition(state, "E"), "S") != (
            automaton.transition(automaton.transition(state, "S"), "E")
        ):
            raise AssertionError("horizontal and vertical transfers do not commute")
        errors = agar.verify_window(automaton.canonical_window(state))
        if errors:
            canonical_errors.append([list(state), errors])
    if canonical_errors:
        raise AssertionError(f"canonical state checks failed: {canonical_errors[:1]}")

    transition_payload = json.dumps(transitions, separators=(",", ":"))
    return {
        "format": "component-agar-transfer-certificate-v1",
        "name": agar.name,
        "period": [agar.period_x, agar.period_y],
        "motif": [list(cell) for cell in sorted(agar.motif, key=lambda p: (p[1], p[0]))],
        "uniform_margin_bound": agar.diameter,
        "state": ["left_phase", "right_phase", "top_phase", "bottom_phase"],
        "alphabet": ["E", "S"],
        "state_count": len(states),
        "initial_state_count": len(list(automaton.initial_states())),
        "transition_count": len(transitions),
        "transition_sha256": hashlib.sha256(transition_payload.encode()).hexdigest(),
        "checks": {
            "finite_motif_still_life": True,
            "minimum_copy_chebyshev_separation": agar.copy_separation(),
            "periodic_tile_still_life": True,
            "transitions_closed": True,
            "transfers_commute": True,
            "canonical_states_verified": len(states),
        },
    }


def agar_from_certificate(certificate: dict[str, object]) -> ComponentAgar:
    period_x, period_y = certificate["period"]
    motif = frozenset(tuple(cell) for cell in certificate["motif"])
    return ComponentAgar(motif, period_x, period_y, certificate["name"])


def verify_transfer_certificate(certificate: object) -> list[str]:
    if not isinstance(certificate, dict):
        return ["certificate must be an object"]
    try:
        agar = agar_from_certificate(certificate)
        expected = analyze_component_agar(agar)
    except (KeyError, TypeError, ValueError) as error:
        return [f"malformed certificate: {error}"]
    if certificate != expected:
        return ["certificate does not match the recomputed transfer analysis"]
    return []


def block_agar(period_x: int = 4, period_y: int = 4) -> ComponentAgar:
    if period_x < 4 or period_y < 4:
        raise ValueError("block-agar theorem requires both periods at least 4")
    return ComponentAgar(
        frozenset({(0, 0), (1, 0), (0, 1), (1, 1)}),
        period_x,
        period_y,
        f"separated-block-{period_x}x{period_y}",
    )
