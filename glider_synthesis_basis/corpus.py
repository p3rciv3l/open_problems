"""Rewindable, independently verified two-glider collision components."""
from dataclasses import dataclass

from .analysis import bounded_closure
from .life import Pattern, run, trajectory, translate
from .model import Box, DIHEDRAL, LocalMove, TimedGlider, verify_move
from .reactions import G_SE


@dataclass(frozen=True)
class RewindCertificate:
    cycles: int
    past_state: Pattern


@dataclass(frozen=True)
class CandidateBasisReport:
    reaction_classes: int
    exact_contexts_from_empty: int
    output_population_spectrum: tuple[int, ...]
    supports_certified_independent_embedding: bool
    universal_claim: bool = False


def _oriented(index: int) -> Pattern:
    return frozenset(DIHEDRAL[index](cell) for cell in G_SE)


def _velocity(cells: Pattern) -> tuple[int, int]:
    after_four = run(cells, 4)
    for dx, dy in ((-1, -1), (-1, 1), (1, -1), (1, 1)):
        if translate(cells, dx, dy) == after_four:
            return dx, dy
    raise ValueError("pattern is not a glider")


def certify_rewindable(move: LocalMove, cycles: int = 10) -> RewindCertificate:
    """Verify that input gliders autonomously approach for 4*cycles ticks."""
    if move.input_context or len(move.input_gliders) != 2:
        raise ValueError("certificate currently covers context-free two-glider collisions")
    velocities = tuple(_velocity(glider.cells) for glider in move.input_gliders)
    if velocities[0] == velocities[1]:
        raise ValueError("parallel co-directional gliders are not rewindable collisions")
    past_gliders = tuple(
        translate(glider.cells, -cycles * dx, -cycles * dy)
        for glider, (dx, dy) in zip(move.input_gliders, velocities)
    )
    past = past_gliders[0] | past_gliders[1]
    if len(past) != 10 or run(past, 4 * cycles) != move.initial_state:
        raise ValueError("gliders do not rewind to an autonomous approach")
    return RewindCertificate(cycles, past)


def _reaction(
    name: str,
    duration: int,
    first_orientation: int,
    second_orientation: int,
    offset: tuple[int, int],
    output: tuple[tuple[int, int], ...],
    activity_box: tuple[int, int, int, int],
) -> LocalMove:
    second = translate(_oriented(second_orientation), *offset)
    move = LocalMove(
        name=name,
        duration=duration,
        input_context=frozenset(),
        input_gliders=(
            TimedGlider(0, _oriented(first_orientation)),
            TimedGlider(0, second),
        ),
        output_context=frozenset(output),
        output_gliders=(),
        affected_box=Box(*activity_box),
    )
    verification = verify_move(move)
    if not verification.valid or verification.activity_box != move.affected_box:
        raise AssertionError(f"invalid corpus reaction {name}: {verification.errors}")
    certify_rewindable(move)
    return move


REWINDABLE_TWO_GLIDER_CORPUS: tuple[LocalMove, ...] = (
    _reaction("rewindable_annihilation", 13, 0, 1, (5, 4), (), (-1, 0, 5, 7)),
    _reaction(
        "rewindable_block", 4, 0, 1, (6, -2),
        ((1, 2), (1, 3), (2, 2), (2, 3)), (0, -2, 6, 3),
    ),
    _reaction(
        "rewindable_beehive", 7, 0, 4, (6, -3),
        ((1, 3), (2, 2), (2, 4), (3, 2), (3, 4), (4, 3)),
        (0, -3, 6, 4),
    ),
    _reaction(
        "rewindable_loaf", 8, 0, 7, (4, 6),
        ((1, 1), (1, 2), (2, 0), (2, 3), (3, 1), (3, 3), (4, 2)),
        (0, 0, 4, 6),
    ),
    _reaction(
        "rewindable_two_blocks", 5, 0, 4, (6, 0),
        ((1, 2), (1, 3), (2, 2), (2, 3), (4, 2), (4, 3), (5, 2), (5, 3)),
        (0, 0, 6, 3),
    ),
    _reaction(
        "rewindable_skew_blocks", 4, 0, 1, (5, -3),
        ((1, 2), (1, 3), (2, -2), (2, -1), (2, 2), (2, 3), (3, -2), (3, -1)),
        (0, -3, 5, 3),
    ),
    _reaction(
        "rewindable_four_blocks", 17, 0, 2, (0, 7),
        ((-6, 4), (-6, 5), (-5, 4), (-5, 5), (-1, -1), (-1, 0),
         (0, -1), (0, 0), (0, 7), (0, 8), (1, 7), (1, 8),
         (5, 2), (5, 3), (6, 2), (6, 3)),
        (-6, -1, 6, 8),
    ),
    _reaction(
        "rewindable_population_24_constellation", 22, 0, 1, (7, -1),
        ((-2, 2), (-1, 1), (-1, 3), (0, 1), (0, 3), (1, 2),
         (3, -3), (3, -2), (3, 6), (3, 7), (4, -4), (4, -1),
         (4, 5), (4, 8), (5, -3), (5, -2), (5, 6), (5, 7),
         (7, 2), (8, 1), (8, 3), (9, 1), (9, 3), (10, 2)),
        (-3, -5, 11, 9),
    ),
)


def corpus_population_spectrum() -> tuple[int, ...]:
    return tuple(sorted(len(move.output_context) for move in REWINDABLE_TWO_GLIDER_CORPUS))


def candidate_basis_report() -> CandidateBasisReport:
    """Report exact capabilities of the finite B8 collision candidate."""
    closure = bounded_closure(REWINDABLE_TWO_GLIDER_CORPUS, max_steps=1)
    return CandidateBasisReport(
        reaction_classes=len({
            move.canonical_key() for move in REWINDABLE_TWO_GLIDER_CORPUS
        }),
        exact_contexts_from_empty=len(closure.reached),
        output_population_spectrum=corpus_population_spectrum(),
        supports_certified_independent_embedding=True,
    )
