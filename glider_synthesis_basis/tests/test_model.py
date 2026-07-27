import unittest

from glider_synthesis_basis.life import translate
from glider_synthesis_basis.model import DIHEDRAL, TimedGlider, canonical_cells, verify_move
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
        with self.assertRaisesRegex(ValueError, "not a period-four"):
            TimedGlider(0, frozenset({(0, 0), (1, 0), (2, 0), (3, 0), (4, 0)}))

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
