import unittest

from glider_synthesis_basis.analysis import bounded_closure
from glider_synthesis_basis.block_arrays import BlockArrayInstance, assess
from glider_synthesis_basis.reactions import BUILTIN_REACTIONS


class AnalysisTests(unittest.TestCase):
    def setUp(self):
        self.closure = bounded_closure(BUILTIN_REACTIONS, max_steps=3)

    def test_exact_bounded_closure(self):
        counts = sorted(len(state) for state in self.closure.reached)
        self.assertEqual(counts, [0, 4, 5, 8])

    def test_two_step_witness_for_specific_two_block_array(self):
        instance = BlockArrayInstance(1, 2, horizontal_gap=4)
        finding = assess(instance, self.closure)
        self.assertTrue(finding.reachable_in_supplied_graph)
        self.assertEqual(finding.witness, (
            "two_gliders_to_block",
            "block_plus_two_gliders_to_two_blocks",
        ))
        self.assertFalse(finding.implies_finite_basis_theorem)

    def test_unreached_array_is_not_reported_as_impossible(self):
        instance = BlockArrayInstance(2, 2)
        finding = assess(instance, self.closure)
        self.assertFalse(finding.reachable_in_supplied_graph)
        self.assertIsNone(finding.witness)
        self.assertFalse(finding.implies_finite_basis_theorem)

    def test_block_array_validates_dimensions_and_spacing(self):
        with self.assertRaises(ValueError):
            BlockArrayInstance(0, 1)
        with self.assertRaises(ValueError):
            BlockArrayInstance(1, 1, horizontal_gap=0)
        self.assertTrue(BlockArrayInstance(3, 4).is_still_life)

    def test_depth_bound_is_enforced(self):
        shallow = bounded_closure(BUILTIN_REACTIONS, max_steps=1)
        self.assertEqual(sorted(len(state) for state in shallow.reached), [0, 4, 5])


if __name__ == "__main__":
    unittest.main()
