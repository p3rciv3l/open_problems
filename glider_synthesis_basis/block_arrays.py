"""Finite m-by-n arrays of blocks, kept separate from move-basis claims."""
from dataclasses import dataclass

from .analysis import ReachabilityResult
from .life import Pattern, is_still_life


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
