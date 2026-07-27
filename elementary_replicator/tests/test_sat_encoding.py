import unittest

from elementary_replicator.direct_search import search
from elementary_replicator.sat_clean_doubling import exclude_scope


class SatEncodingTests(unittest.TestCase):
    def test_selected_beyond_three_by_three_scopes_are_unsat(self):
        for width, height, time in ((4, 4, 2), (5, 3, 2), (6, 6, 3)):
            result = exclude_scope(width, height, time)
            self.assertGreater(result.offset_pairs, 0)
            self.assertFalse(result.satisfiable)

    def test_geometrically_impossible_scope_has_no_pairs(self):
        result = exclude_scope(4, 4, 1)
        self.assertEqual(result.offset_pairs, 0)
        self.assertFalse(result.satisfiable)

    def test_independent_explicit_state_scope_is_empty(self):
        result = search(max_side=3, max_time=2)
        self.assertEqual((result.seeds, result.cases), (365, 730))
        self.assertEqual(result.witnesses, ())


if __name__ == "__main__":
    unittest.main()
