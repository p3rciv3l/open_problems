"""Canonical bounded local-rewrite data model."""
from dataclasses import dataclass, replace
from typing import Callable

from .life import Cell, Pattern, is_still_life, step, trajectory, translate

Transform = Callable[[Cell], Cell]
DIHEDRAL: tuple[Transform, ...] = (
    lambda p: (p[0], p[1]),
    lambda p: (-p[1], p[0]),
    lambda p: (-p[0], -p[1]),
    lambda p: (p[1], -p[0]),
    lambda p: (-p[0], p[1]),
    lambda p: (p[0], -p[1]),
    lambda p: (p[1], p[0]),
    lambda p: (-p[1], -p[0]),
)


def transform_cells(cells: Pattern, transform: Transform) -> Pattern:
    return frozenset(transform(cell) for cell in cells)


def canonical_cells(cells: Pattern) -> tuple[Cell, ...]:
    if not cells:
        return ()
    candidates = []
    for transform in DIHEDRAL:
        changed = transform_cells(cells, transform)
        min_x = min(x for x, _ in changed)
        min_y = min(y for _, y in changed)
        candidates.append(tuple(sorted(translate(changed, -min_x, -min_y))))
    return min(candidates)


@dataclass(frozen=True, order=True)
class Box:
    min_x: int
    min_y: int
    max_x: int
    max_y: int

    def __post_init__(self) -> None:
        if self.min_x > self.max_x or self.min_y > self.max_y:
            raise ValueError("box minima must not exceed maxima")

    def contains(self, cell: Cell) -> bool:
        x, y = cell
        return self.min_x <= x <= self.max_x and self.min_y <= y <= self.max_y

    @property
    def corners(self) -> Pattern:
        return frozenset({
            (self.min_x, self.min_y), (self.min_x, self.max_y),
            (self.max_x, self.min_y), (self.max_x, self.max_y),
        })

    def transformed(self, transform: Transform) -> "Box":
        corners = transform_cells(self.corners, transform)
        return Box(
            min(x for x, _ in corners), min(y for _, y in corners),
            max(x for x, _ in corners), max(y for _, y in corners),
        )

    def translated(self, dx: int, dy: int) -> "Box":
        return Box(
            self.min_x + dx, self.min_y + dy,
            self.max_x + dx, self.max_y + dy,
        )


@dataclass(frozen=True)
class TimedGlider:
    """A five-cell glider phase observed at a rewrite-boundary generation."""

    generation: int
    cells: Pattern

    def __post_init__(self) -> None:
        object.__setattr__(self, "cells", frozenset(self.cells))
        if len(self.cells) != 5:
            raise ValueError("a glider phase has exactly five live cells")
        after_four = trajectory(self.cells, 4)[-1]
        shifts = {
            (x2 - x1, y2 - y1)
            for x1, y1 in self.cells
            for x2, y2 in after_four
        }
        if not any(translate(self.cells, dx, dy) == after_four for dx, dy in shifts):
            raise ValueError("cells are not a period-four translating glider")

    def transformed(self, transform: Transform) -> "TimedGlider":
        return TimedGlider(self.generation, transform_cells(self.cells, transform))

    def translated(self, dx: int, dy: int) -> "TimedGlider":
        return TimedGlider(self.generation, translate(self.cells, dx, dy))


@dataclass(frozen=True)
class LocalMove:
    name: str
    duration: int
    input_context: Pattern
    input_gliders: tuple[TimedGlider, ...]
    output_context: Pattern
    output_gliders: tuple[TimedGlider, ...]
    affected_box: Box

    def __post_init__(self) -> None:
        object.__setattr__(self, "input_context", frozenset(self.input_context))
        object.__setattr__(self, "output_context", frozenset(self.output_context))
        object.__setattr__(self, "input_gliders", tuple(self.input_gliders))
        object.__setattr__(self, "output_gliders", tuple(self.output_gliders))
        if self.duration < 0:
            raise ValueError("duration must be non-negative")
        if not is_still_life(self.input_context):
            raise ValueError("input context is not a still life")
        if not is_still_life(self.output_context):
            raise ValueError("output context is not a still life")
        if any(g.generation != 0 for g in self.input_gliders):
            raise ValueError("input gliders must be observed at generation zero")
        if any(g.generation != self.duration for g in self.output_gliders):
            raise ValueError("output gliders must be observed at move duration")
        self._boundary_state(self.input_context, self.input_gliders)
        self._boundary_state(self.output_context, self.output_gliders)

    @staticmethod
    def _boundary_state(context: Pattern, gliders: tuple[TimedGlider, ...]) -> Pattern:
        parts = [context, *(glider.cells for glider in gliders)]
        union = frozenset().union(*parts)
        if len(union) != sum(len(part) for part in parts):
            raise ValueError("boundary components overlap")
        return union

    @property
    def initial_state(self) -> Pattern:
        return self._boundary_state(self.input_context, self.input_gliders)

    @property
    def expected_state(self) -> Pattern:
        return self._boundary_state(self.output_context, self.output_gliders)

    def transformed(self, transform: Transform) -> "LocalMove":
        return replace(
            self,
            input_context=transform_cells(self.input_context, transform),
            input_gliders=tuple(g.transformed(transform) for g in self.input_gliders),
            output_context=transform_cells(self.output_context, transform),
            output_gliders=tuple(g.transformed(transform) for g in self.output_gliders),
            affected_box=self.affected_box.transformed(transform),
        )

    def translated(self, dx: int, dy: int) -> "LocalMove":
        return replace(
            self,
            input_context=translate(self.input_context, dx, dy),
            input_gliders=tuple(g.translated(dx, dy) for g in self.input_gliders),
            output_context=translate(self.output_context, dx, dy),
            output_gliders=tuple(g.translated(dx, dy) for g in self.output_gliders),
            affected_box=self.affected_box.translated(dx, dy),
        )

    def canonical_key(self) -> tuple:
        candidates = []
        for transform in DIHEDRAL:
            move = self.transformed(transform)
            points = (
                move.input_context | move.output_context | move.affected_box.corners |
                frozenset().union(*(g.cells for g in move.input_gliders + move.output_gliders))
            )
            min_x = min(x for x, _ in points)
            min_y = min(y for _, y in points)
            move = move.translated(-min_x, -min_y)
            candidates.append((
                move.duration,
                tuple(sorted(move.input_context)),
                tuple(sorted((g.generation, tuple(sorted(g.cells))) for g in move.input_gliders)),
                tuple(sorted(move.output_context)),
                tuple(sorted((g.generation, tuple(sorted(g.cells))) for g in move.output_gliders)),
                move.affected_box,
            ))
        return min(candidates)

    def canonical(self) -> "LocalMove":
        key = self.canonical_key()
        for transform in DIHEDRAL:
            move = self.transformed(transform)
            points = (
                move.input_context | move.output_context | move.affected_box.corners |
                frozenset().union(*(g.cells for g in move.input_gliders + move.output_gliders))
            )
            min_x = min(x for x, _ in points)
            min_y = min(y for _, y in points)
            candidate = move.translated(-min_x, -min_y)
            if candidate.canonical_key_for_current_frame() == key:
                return candidate
        raise AssertionError("canonical candidate was not found")

    def canonical_key_for_current_frame(self) -> tuple:
        return (
            self.duration,
            tuple(sorted(self.input_context)),
            tuple(sorted((g.generation, tuple(sorted(g.cells))) for g in self.input_gliders)),
            tuple(sorted(self.output_context)),
            tuple(sorted((g.generation, tuple(sorted(g.cells))) for g in self.output_gliders)),
            self.affected_box,
        )


@dataclass(frozen=True)
class Verification:
    move_name: str
    valid: bool
    observed_final: Pattern
    first_stable_generation: int | None
    activity_box: Box
    errors: tuple[str, ...]


def verify_move(move: LocalMove) -> Verification:
    states = trajectory(move.initial_state, move.duration)
    errors = []
    if states[-1] != move.expected_state:
        errors.append("simulated final state differs from declared output")

    outside_baseline = frozenset(c for c in move.input_context if not move.affected_box.contains(c))
    for generation, state in enumerate(states):
        outside = frozenset(c for c in state if not move.affected_box.contains(c))
        if outside != outside_baseline:
            errors.append(f"state outside affected box changed at generation {generation}")
            break

    changed_activity = frozenset().union(*(
        state - outside_baseline for state in states
    ))
    activity_box = Box(
        min(x for x, _ in changed_activity), min(y for _, y in changed_activity),
        max(x for x, _ in changed_activity), max(y for _, y in changed_activity),
    )
    first_stable = next(
        (generation for generation, state in enumerate(states)
         if generation < len(states) - 1 and states[generation + 1] == state),
        None,
    )
    if first_stable is None and step(states[-1]) == states[-1]:
        first_stable = move.duration
    return Verification(
        move.name, not errors, states[-1], first_stable, activity_box, tuple(errors)
    )
