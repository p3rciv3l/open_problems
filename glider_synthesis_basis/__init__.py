"""Bounded experiments for problem 10; this package makes no universal claim."""
from .analysis import ReachabilityResult, bounded_closure
from .block_arrays import (
    SPACED_CONSTRUCTION_MIN_GAP,
    BlockArrayFinding,
    BlockArrayInstance,
    SpacedArrayConstruction,
    assess,
    construct_spaced_block_array,
)
from .corpus import (
    CandidateBasisReport,
    REWINDABLE_TWO_GLIDER_CORPUS,
    RewindCertificate,
    candidate_basis_report,
    certify_rewindable,
)
from .embedding import (
    NoninteractionCertificate,
    certify_noninteraction,
    independent_union,
)
from .model import Box, LocalMove, TimedGlider, Verification, canonical_cells, verify_move
from .published import (
    TwoRowExtensionTheorem,
    certify_two_row_extension_theorem,
    two_row_extension,
)
from .reactions import BUILTIN_REACTIONS, verify_builtins

__all__ = [
    "BUILTIN_REACTIONS", "BlockArrayFinding", "BlockArrayInstance", "Box",
    "CandidateBasisReport", "LocalMove", "NoninteractionCertificate",
    "REWINDABLE_TWO_GLIDER_CORPUS",
    "ReachabilityResult", "RewindCertificate", "SPACED_CONSTRUCTION_MIN_GAP",
    "SpacedArrayConstruction", "TimedGlider", "TwoRowExtensionTheorem",
    "Verification", "assess", "bounded_closure", "candidate_basis_report",
    "canonical_cells",
    "certify_noninteraction", "certify_rewindable",
    "certify_two_row_extension_theorem", "construct_spaced_block_array",
    "independent_union", "two_row_extension", "verify_builtins", "verify_move",
]
