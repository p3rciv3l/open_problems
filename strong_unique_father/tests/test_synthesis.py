from pathlib import Path

from pysat.solvers import Minisat22

from strong_unique_father.life import evolve_finite
from strong_unique_father.patterns import Pattern
from strong_unique_father.sat import finite_counter_predecessor
from strong_unique_father.synthesis import (
    StillLifeCNF,
    synthesize,
    verify_exhaustion_report,
)


def test_still_life_cnf_enumerates_exact_two_by_two_box() -> None:
    cnf = StillLifeCNF(2, 2, symmetry="d4")
    with Minisat22(bootstrap_with=cnf.clauses) as solver:
        assert solver.solve()
        pattern = cnf.pattern(solver.get_model())
        assert pattern.live == frozenset({(0, 0), (1, 0), (0, 1), (1, 1)})
        solver.add_clause(cnf.block_pattern(pattern))
        assert not solver.solve()


def test_finite_counter_predecessor_is_global() -> None:
    block = Pattern(2, 2, frozenset({(0, 0), (1, 0), (0, 1), (1, 1)}))
    assignment = finite_counter_predecessor(
        block.live, block.width, block.height, (0, 0), True
    )
    assert assignment is not None
    predecessor = frozenset(cell for cell, value in assignment.items() if value)
    assert (0, 0) not in predecessor
    assert evolve_finite(predecessor) == block.live


def test_synthesis_exhaustion_exports_recheckable_instance(tmp_path: Path) -> None:
    prefix = tmp_path / "all-live-2x2"
    report = synthesize(2, 2, symmetry="d4", proof_prefix=prefix)
    assert report["exhausted"] is True
    assert report["winner"] is None
    assert report["candidates_rejected_by_global_finite_predecessor"] == 1
    verify_exhaustion_report(report)
    assert prefix.with_suffix(".cnf").read_text().startswith("p cnf 4 44\n")
    assert prefix.with_suffix(".drat").read_text().endswith("0\n")
