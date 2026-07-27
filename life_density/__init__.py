"""Exact optimization of temporally periodic Conway Life configurations."""

from .optimizer import optimize
from .verify import verify_result

__all__ = ["optimize", "verify_result"]

