"""Finite m-by-n arrays of blocks, kept separate from move-basis claims."""
from dataclasses import dataclass

from .analysis import ReachabilityResult
from .corpus import REWINDABLE_TWO_GLIDER_CORPUS
from .embedding import independent_union
from .life import Pattern, is_still_life
from .model import LocalMove, verify_move

SPACED_CONSTRUCTION_MIN_GAP = 6


@dataclass(frozen=True)
class BlockArrayInstance:
    rows: int
    columns: int
    horizontal_gap: int = 1
    vertical_gap: int = 1
    origin: tuple[int, int] = (0, 0)

    def __post_init__(self) -> None:
        if self.rows < 1 or self.columns < 1:
            raise ValueError("rows and columns must be positive")
        if self.horizontal_gap < 1 or self.vertical_gap < 1:
            raise ValueError("separate blocks need gaps of at least one cell")

    @property
    def cells(self) -> Pattern:
        ox, oy = self.origin
        pitch_x = 2 + self.horizontal_gap
        pitch_y = 2 + self.vertical_gap
        return frozenset(
            (ox + column * pitch_x + dx, oy + row * pitch_y + dy)
            for row in range(self.rows)
            for column in range(self.columns)
            for dx in (0, 1)
            for dy in (0, 1)
        )

    @property
    def is_still_life(self) -> bool:
        return is_still_life(self.cells)


@dataclass(frozen=True)
class BlockArrayFinding:
    instance: BlockArrayInstance
    reachable_in_supplied_graph: bool
    witness: tuple[str, ...] | None
    implies_finite_basis_theorem: bool = False


def assess(instance: BlockArrayInstance, closure: ReachabilityResult) -> BlockArrayFinding:
    """Ask only whether this exact finite instance occurs in this finite graph."""
    witness = closure.path_to(instance.cells)
    return BlockArrayFinding(instance, witness is not None, witness)


@dataclass(frozen=True)
class SpacedArrayConstruction:
    """A certified simultaneous synthesis for one finite block array."""

    instance: BlockArrayInstance
    move: LocalMove
    glider_count: int


def construct_spaced_block_array(
    instance: BlockArrayInstance,
) -> SpacedArrayConstruction:
    """Construct any m×n array whose relevant inter-block gaps are at least six.

    Copies of the rewindable two-glider block reaction are translated to the
    requested block positions. Their complete traces satisfy the
    distance-three noninteraction lemma, so ``independent_union`` proves the
    simultaneous composition rather than merely testing its final state.
    """
    if instance.columns > 1 and instance.horizontal_gap < SPACED_CONSTRUCTION_MIN_GAP:
        raise ValueError("horizontal gap is too small for certified independent synthesis")
    if instance.rows > 1 and instance.vertical_gap < SPACED_CONSTRUCTION_MIN_GAP:
        raise ValueError("vertical gap is too small for certified independent synthesis")

    block_move = next(
        move
        for move in REWINDABLE_TWO_GLIDER_CORPUS
        if move.name == "rewindable_block"
    )
    ox, oy = instance.origin
    pitch_x = 2 + instance.horizontal_gap
    pitch_y = 2 + instance.vertical_gap
    copies = tuple(
        block_move.translated(
            ox + column * pitch_x - 1,
            oy + row * pitch_y - 2,
        )
        for row in range(instance.rows)
        for column in range(instance.columns)
    )
    move = independent_union(
        f"certified_{instance.rows}x{instance.columns}_spaced_block_array",
        copies,
    )
    result = verify_move(move)
    if not result.valid or move.output_context != instance.cells:
        raise AssertionError(f"invalid spaced-array construction: {result.errors}")
    return SpacedArrayConstruction(instance, move, 2 * instance.rows * instance.columns)
