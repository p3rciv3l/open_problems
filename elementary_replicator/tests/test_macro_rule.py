import unittest

from elementary_replicator.sat_macro_rule import (
    MacroGeometry,
    PARITY_RULES,
    outside_context_is_excluded,
    solve_macro_rule,
)
from elementary_replicator.macro_verify import exhaustive_tiles, verify_macro_tile


class MacroRuleTests(unittest.TestCase):
    def test_context_cone_condition(self):
        self.assertTrue(outside_context_is_excluded(MacroGeometry(3, 2, 4, 4)))
        self.assertFalse(outside_context_is_excluded(MacroGeometry(3, 2, 4, 6)))

    def test_small_rule_90_macro_tile_is_unsat(self):
        geometry = MacroGeometry(2, 2, 3, 3)
        for rule in PARITY_RULES:
            with self.subTest(rule=rule):
                result = solve_macro_rule(geometry, rule)
                self.assertFalse(result.satisfiable)
                self.assertIsNone(result.tile)
                self.assertEqual(exhaustive_tiles(geometry, rule), ())

    def test_rule_must_preserve_zero_background(self):
        with self.assertRaisesRegex(ValueError, "000 -> 0"):
            solve_macro_rule(MacroGeometry(2, 2, 3, 3), 91)

    def test_sat_encoding_finds_independently_verified_identity_tile(self):
        geometry = MacroGeometry(2, 2, 4, 1)
        result = solve_macro_rule(geometry, 204)
        self.assertTrue(result.satisfiable)
        self.assertEqual(
            result.tile,
            frozenset({(0, 0), (1, 0), (0, 1), (1, 1)}),
        )
        self.assertTrue(verify_macro_tile(result.tile, geometry, 204))


if __name__ == "__main__":
    unittest.main()
