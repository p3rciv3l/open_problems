"""Bounded experiments for problem 10; this package makes no universal claim."""
from .analysis import ReachabilityResult, bounded_closure
from .block_arrays import BlockArrayFinding, BlockArrayInstance, assess
from .model import Box, LocalMove, TimedGlider, Verification, canonical_cells, verify_move
from .reactions import BUILTIN_REACTIONS, verify_builtins

__all__ = [
    "BUILTIN_REACTIONS", "BlockArrayFinding", "BlockArrayInstance", "Box",
    "LocalMove", "ReachabilityResult", "TimedGlider", "Verification", "assess",
    "bounded_closure", "canonical_cells", "verify_builtins", "verify_move",
]
