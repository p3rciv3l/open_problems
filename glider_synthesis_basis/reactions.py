"""A small built-in corpus; every entry is checked by the simulator."""
from .life import Pattern
from .model import Box, LocalMove, TimedGlider, Verification, verify_move

G_SE: Pattern = frozenset({(0, 2), (1, 0), (1, 2), (2, 1), (2, 2)})
G_SW: Pattern = frozenset({(-2, 0), (-2, 1), (-2, 2), (-1, 2), (0, 1)})
G_NW_MIRRORED: Pattern = frozenset({(-2, 1), (-2, 2), (-1, 0), (-1, 2), (0, 2)})
BLOCK: Pattern = frozenset({(0, 0), (0, 1), (1, 0), (1, 1)})


def _shift(cells: Pattern, dx: int, dy: int) -> Pattern:
    return frozenset((x + dx, y + dy) for x, y in cells)


def _two_glider_block() -> LocalMove:
    return LocalMove(
        name="two_gliders_to_block",
        duration=8,
        input_context=frozenset(),
        input_gliders=(
            TimedGlider(0, G_SE),
            TimedGlider(0, _shift(G_SE, -3, 2)),
        ),
        output_context=frozenset({(2, 2), (2, 3), (3, 2), (3, 3)}),
        output_gliders=(),
        affected_box=Box(-3, 0, 3, 5),
    )


def _two_glider_boat() -> LocalMove:
    return LocalMove(
        name="two_gliders_to_boat",
        duration=8,
        input_context=frozenset(),
        input_gliders=(
            TimedGlider(0, G_SW),
            TimedGlider(0, _shift(G_NW_MIRRORED, -2, -3)),
        ),
        output_context=frozenset({
            (-3, -2), (-3, -1), (-2, -2), (-2, 0), (-1, -1),
        }),
        output_gliders=(),
        affected_box=Box(-4, -3, 0, 3),
    )


def _block_plus_two_gliders_to_two_blocks() -> LocalMove:
    preserved = _shift(BLOCK, 8, 2)
    return LocalMove(
        name="block_plus_two_gliders_to_two_blocks",
        duration=8,
        input_context=preserved,
        input_gliders=(
            TimedGlider(0, G_SE),
            TimedGlider(0, _shift(G_SE, -3, 2)),
        ),
        output_context=(
            preserved | frozenset({(2, 2), (2, 3), (3, 2), (3, 3)})
        ),
        output_gliders=(),
        affected_box=Box(-3, 0, 3, 5),
    )


BUILTIN_REACTIONS: tuple[LocalMove, ...] = (
    _two_glider_block(),
    _two_glider_boat(),
    _block_plus_two_gliders_to_two_blocks(),
)


def verify_builtins() -> tuple[Verification, ...]:
    """Simulate each corpus entry independently from its declared input."""
    return tuple(verify_move(move) for move in BUILTIN_REACTIONS)
