"""Certified noninteraction and simultaneous local-move embedding.

For Life's radius-one rule, if two independently evolved patterns remain at
Chebyshev distance at least three, no radius-one neighbourhood contains live
cells from both patterns. Consequently one Life step distributes over their
union. Induction proves that the union trace is exactly the union of the two
traces. ``certify_noninteraction`` checks the lemma's finite hypothesis;
``independent_union`` applies its conclusion to local moves.
"""
from dataclasses import dataclass

from .life import Pattern, trajectory
from .model import Box, LocalMove


@dataclass(frozen=True)
class NoninteractionCertificate:
    duration: int
    minimum_separation: int
    separation_by_generation: tuple[int, ...]


def chebyshev_separation(left: Pattern, right: Pattern) -> int:
    if not left or not right:
        return 10**18
    return min(
        max(abs(x1 - x2), abs(y1 - y2))
        for x1, y1 in left
        for x2, y2 in right
    )


def certify_noninteraction(
    left: Pattern,
    right: Pattern,
    duration: int,
) -> NoninteractionCertificate:
    """Certify the distance-three sufficient condition through ``duration``."""
    left_trace = trajectory(left, duration)
    right_trace = trajectory(right, duration)
    separations = tuple(
        chebyshev_separation(left_state, right_state)
        for left_state, right_state in zip(left_trace, right_trace)
    )
    minimum = min(separations)
    if minimum < 3:
        raise ValueError(f"traces are not certified independent: separation {minimum} < 3")

    union_trace = trajectory(left | right, duration)
    expected = tuple(a | b for a, b in zip(left_trace, right_trace))
    if union_trace != expected:
        raise AssertionError("Life violated the certified noninteraction lemma")
    return NoninteractionCertificate(duration, minimum, separations)


def _box_hull(boxes: tuple[Box, ...]) -> Box:
    return Box(
        min(box.min_x for box in boxes),
        min(box.min_y for box in boxes),
        max(box.max_x for box in boxes),
        max(box.max_y for box in boxes),
    )


def independent_union(name: str, moves: tuple[LocalMove, ...]) -> LocalMove:
    """Compose equal-duration moves when every pair satisfies the lemma."""
    if not moves:
        raise ValueError("at least one move is required")
    duration = moves[0].duration
    if any(move.duration != duration for move in moves):
        raise ValueError("independent moves must have equal durations")
    for index, left in enumerate(moves):
        for right in moves[index + 1:]:
            certify_noninteraction(left.initial_state, right.initial_state, duration)

    return LocalMove(
        name=name,
        duration=duration,
        input_context=frozenset().union(*(move.input_context for move in moves)),
        input_gliders=tuple(
            glider for move in moves for glider in move.input_gliders
        ),
        output_context=frozenset().union(*(move.output_context for move in moves)),
        output_gliders=tuple(
            glider for move in moves for glider in move.output_gliders
        ),
        affected_box=_box_hull(tuple(move.affected_box for move in moves)),
    )
