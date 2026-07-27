import unittest

from glider_synthesis_basis.life import is_still_life, translate
from glider_synthesis_basis.model import (
    DIHEDRAL,
    Box,
    LocalMove,
    TimedGlider,
    canonical_cells,
    verify_move,
)
from glider_synthesis_basis.reactions import BUILTIN_REACTIONS, G_SE


class ModelTests(unittest.TestCase):
    def test_canonical_cells_quotients_translation_and_dihedral_group(self):
        expected = canonical_cells(G_SE)
        for transform in DIHEDRAL:
            changed = frozenset(transform(cell) for cell in G_SE)
            self.assertEqual(canonical_cells(translate(changed, 23, -17)), expected)

    def test_move_key_quotients_translation_and_dihedral_group(self):
        move = BUILTIN_REACTIONS[0]
        expected = move.canonical_key()
        for transform in DIHEDRAL:
            self.assertEqual(
                move.transformed(transform).translated(19, -31).canonical_key(),
                expected,
            )

    def test_canonical_is_idempotent(self):
        move = BUILTIN_REACTIONS[2]
        canonical = move.canonical()
        self.assertEqual(canonical.canonical_key(), move.canonical_key())
        self.assertEqual(canonical.canonical(), canonical)

    def test_non_glider_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "one-cell diagonal"):
            TimedGlider(0, frozenset({(0, 0), (1, 0), (2, 0), (3, 0), (4, 0)}))

    def test_five_cell_boat_still_life_is_not_a_glider(self):
        boat = frozenset({(0, 0), (0, 1), (1, 0), (1, 2), (2, 1)})
        self.assertTrue(is_still_life(boat))
        with self.assertRaisesRegex(ValueError, "one-cell diagonal"):
            TimedGlider(0, boat)

    def test_quiescent_identity_uses_declared_box_as_activity_fallback(self):
        declared_box = Box(10, 20, 12, 24)
        cases = (
            ("empty_identity", frozenset(), 0),
            (
                "still_life_identity",
                frozenset({(0, 0), (0, 1), (1, 0), (1, 1)}),
                3,
            ),
        )
        for name, context, duration in cases:
            with self.subTest(move=name):
                move = LocalMove(
                    name=name,
                    duration=duration,
                    input_context=context,
                    input_gliders=(),
                    output_context=context,
                    output_gliders=(),
                    affected_box=declared_box,
                )
                result = verify_move(move)
                self.assertTrue(result.valid, result.errors)
                self.assertEqual(result.observed_final, context)
                self.assertEqual(result.first_stable_generation, 0)
                self.assertEqual(result.activity_box, declared_box)

    def test_each_builtin_is_independently_simulated(self):
        for move in BUILTIN_REACTIONS:
            with self.subTest(move=move.name):
                result = verify_move(move)
                self.assertTrue(result.valid, result.errors)
                self.assertEqual(result.observed_final, move.expected_state)
                self.assertEqual(result.first_stable_generation, move.duration)
                self.assertEqual(result.activity_box, move.affected_box)


if __name__ == "__main__":
    unittest.main()
