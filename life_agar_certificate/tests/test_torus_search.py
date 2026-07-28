import json
import unittest
from pathlib import Path

from pysat.solvers import Solver

from torus_search import TorusCNF, decode
from torus_verify import step, verify_candidate


class TorusSearchTest(unittest.TestCase):
    def test_periodic_candidate_replays(self):
        search = TorusCNF(4, 4, 1)
        cnf = search.at_least(8)
        with Solver(name="g4", bootstrap_with=cnf.clauses) as solver:
            self.assertTrue(solver.solve())
            phases = decode(solver.get_model(), search)
        self.assertEqual(step(phases[0]), phases[0])

    def test_above_half_is_unsat_on_three_torus(self):
        search = TorusCNF(3, 3, 1)
        with Solver(name="g4", bootstrap_with=search.at_least(5).clauses) as solver:
            self.assertFalse(solver.solve())

    def test_stored_five_torus_equality_witness(self):
        path = Path(__file__).parents[1] / "torus_results.json"
        records = json.loads(path.read_text())["instances"]
        record = next(
            item
            for item in records
            if (item["width"], item["height"], item["period"]) == (5, 5, 2)
        )
        verify_candidate(record)
        self.assertEqual(record["maximum_density"], "25/50")
        self.assertEqual(record["phase_populations"], [13, 12])


if __name__ == "__main__":
    unittest.main()
