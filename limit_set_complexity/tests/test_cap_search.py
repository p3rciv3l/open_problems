import itertools
import unittest

from cap_search import (
    Domain,
    band_value,
    cap_cells,
    clause_count,
    dimensions,
    instance_clauses,
    relation_clauses,
)
from forcing import OFFSETS, life


def clause_holds(clause, assignment):
    return any((literal > 0) == assignment[abs(literal)] for literal in clause)


class CapEncoderTests(unittest.TestCase):
    def test_relation_cnf_matches_life_truth_table(self):
        inputs = list(range(1, 10))
        output = 10
        clauses = list(relation_clauses(inputs, output))
        center_index = OFFSETS.index((0, 0))
        for bits in itertools.product((0, 1), repeat=9):
            expected = life(
                bits[center_index],
                bits[:center_index] + bits[center_index + 1 :],
            )
            for output_bit in (0, 1):
                assignment = dict(zip(inputs, bits))
                assignment[output] = output_bit
                accepts = all(clause_holds(c, assignment) for c in clauses)
                self.assertEqual(accepts, output_bit == expected)

    def test_marching_band_is_fixed_by_two_life_steps(self):
        first = {}
        for y in range(-1, 5):
            for x in range(-1, 9):
                neighbors = [
                    band_value(x + dx, y + dy)
                    for dx, dy in OFFSETS
                    if (dx, dy) != (0, 0)
                ]
                first[x, y] = life(band_value(x, y), neighbors)
        for y in range(4):
            for x in range(8):
                neighbors = [
                    first[x + dx, y + dy]
                    for dx, dy in OFFSETS
                    if (dx, dy) != (0, 0)
                ]
                self.assertEqual(life(first[x, y], neighbors), band_value(x, y))

    def test_variable_layers_are_disjoint(self):
        domain = Domain(8, 4)
        predecessor = {
            domain.predecessor_var(x, y)
            for y in domain.predecessor_y
            for x in domain.predecessor_x
        }
        middle = {
            domain.middle_var(x, y)
            for y in domain.middle_y
            for x in domain.middle_x
        }
        self.assertFalse(predecessor & middle)
        self.assertEqual(len(predecessor | middle), domain.variables)

    def test_published_cap_geometry(self):
        domain = dimensions(20)
        self.assertEqual((domain.width, domain.height), (48, 44))
        cells = cap_cells(domain)
        self.assertEqual(min(x for x, _ in cells), 10)
        self.assertEqual(max(x for x, _ in cells), 29)
        self.assertEqual(min(y for _, y in cells), -1)
        self.assertEqual(max(y for _, y in cells), 44)
        self.assertEqual(len(cells), 20 * 46)

    def test_candidate_clause_count(self):
        self.assertEqual(clause_count(dimensions(15)), 1_034_392)
        tiny = Domain(1, 1)
        self.assertEqual(
            clause_count(tiny), sum(1 for _ in instance_clauses(tiny))
        )


if __name__ == "__main__":
    unittest.main()
