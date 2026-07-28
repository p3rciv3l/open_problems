import itertools
import unittest

from forcing import (
    CENTER_TILE,
    KOYNNOS,
    OFFSETS,
    agar_value,
    coordinate,
    life,
    local_forbidden_clauses,
    variable,
    verify_phase,
)


def clause_holds(clause, assignment):
    return any((literal > 0) == assignment[abs(literal)] for literal in clause)


class EncodingTests(unittest.TestCase):
    def test_variable_round_trip(self):
        for coordinate_value in [(-1, -1), (0, 0), (12, 12), (30, 27)]:
            self.assertEqual(coordinate(variable(*coordinate_value)), coordinate_value)

    def test_local_cnf_matches_direct_life_truth_table(self):
        variables = [variable(dx, dy) for dx, dy in OFFSETS]
        center_index = OFFSETS.index((0, 0))
        for output in (0, 1):
            clauses = list(local_forbidden_clauses(0, 0, output))
            for bits in itertools.product((0, 1), repeat=9):
                assignment = dict(zip(variables, bits))
                cnf_accepts = all(clause_holds(c, assignment) for c in clauses)
                actual = life(
                    bits[center_index],
                    bits[:center_index] + bits[center_index + 1 :],
                )
                self.assertEqual(cnf_accepts, actual == output)

    def test_koynnos_is_a_life_fixed_point(self):
        for y in range(3):
            for x in range(6):
                neighbors = [
                    agar_value(x + dx, y + dy)
                    for dx, dy in OFFSETS
                    if (dx, dy) != (0, 0)
                ]
                self.assertEqual(life(agar_value(x, y), neighbors), KOYNNOS[y][x])

    def test_paper_phase_forces_central_tile(self):
        result = verify_phase(0, 0)
        self.assertTrue(result.baseline_sat)
        self.assertEqual(result.forced_cells, len(CENTER_TILE))
        self.assertEqual(result.opposite_queries_unsat, len(CENTER_TILE))


if __name__ == "__main__":
    unittest.main()
