import unittest

from glider_synthesis_basis.block_arrays import (
    BlockArrayInstance,
    construct_spaced_block_array,
)
from glider_synthesis_basis.model import verify_move
from glider_synthesis_basis.published import (
    certify_two_row_extension_theorem,
    two_row_extension,
)


class ConstructionTests(unittest.TestCase):
    def test_arbitrary_dimension_spaced_array_constructor(self):
        for rows, columns in ((1, 1), (1, 5), (3, 4), (4, 2)):
            with self.subTest(rows=rows, columns=columns):
                instance = BlockArrayInstance(
                    rows, columns, horizontal_gap=6, vertical_gap=6
                )
                construction = construct_spaced_block_array(instance)
                self.assertEqual(construction.move.output_context, instance.cells)
                self.assertEqual(construction.glider_count, 2 * rows * columns)
                self.assertTrue(verify_move(construction.move).valid)

    def test_constructor_does_not_claim_standard_gap_arrays(self):
        with self.assertRaisesRegex(ValueError, "gap is too small"):
            construct_spaced_block_array(BlockArrayInstance(2, 2))

    def test_published_extension_component(self):
        move = two_row_extension(4)
        self.assertEqual(len(move.input_gliders), 8)
        self.assertEqual(len(move.output_context), 40)
        self.assertEqual(move.duration, 68)
        self.assertTrue(verify_move(move).valid)

    def test_two_row_induction_is_finite_checked_then_local(self):
        theorem = certify_two_row_extension_theorem()
        self.assertEqual(theorem.directly_verified_widths, tuple(range(4, 30)))
        self.assertEqual(theorem.duration, 68)
        self.assertEqual(theorem.locality_cutoff_width, 29)
        self.assertEqual(theorem.locality_margin, 2)


if __name__ == "__main__":
    unittest.main()
