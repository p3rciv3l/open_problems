"""Finite, exact-state closure and reachability over a supplied move set."""
from collections import deque
from dataclasses import dataclass

from .life import Pattern
from .model import LocalMove, canonical_cells

State = tuple[tuple[int, int], ...]


@dataclass(frozen=True)
class ReachabilityResult:
    seed: State
    max_steps: int
    witnesses: dict[State, tuple[str, ...]]

    @property
    def reached(self) -> frozenset[State]:
        return frozenset(self.witnesses)

    def path_to(self, cells: Pattern) -> tuple[str, ...] | None:
        return self.witnesses.get(canonical_cells(cells))


def bounded_closure(
    moves: tuple[LocalMove, ...],
    seed: Pattern = frozenset(),
    max_steps: int = 10,
) -> ReachabilityResult:
    """Apply whole-context rules exactly; no subpattern embedding is inferred."""
    if max_steps < 0:
        raise ValueError("max_steps must be non-negative")
    edges: dict[State, list[tuple[State, str]]] = {}
    for move in moves:
        source = canonical_cells(move.input_context)
        target = canonical_cells(move.output_context)
        edges.setdefault(source, []).append((target, move.name))

    start = canonical_cells(seed)
    witnesses: dict[State, tuple[str, ...]] = {start: ()}
    queue = deque([(start, 0)])
    while queue:
        state, depth = queue.popleft()
        if depth == max_steps:
            continue
        for target, name in edges.get(state, ()):
            if target not in witnesses:
                witnesses[target] = witnesses[state] + (name,)
                queue.append((target, depth + 1))
    return ReachabilityResult(start, max_steps, witnesses)
