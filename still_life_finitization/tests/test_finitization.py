import copy
import unittest

from still_life.pattern import PeriodicPattern, Window
from still_life.sat import build_encoding, enumerate_margins
from still_life.verify import verify_witness


class PatternTests(unittest.TestCase):
    def test_periodic_validation(self):
        block = PeriodicPattern(("11..", "11..", "....", "...."), "block")
        self.assertEqual(block.validate_still_life(), [])
        self.assertTrue(PeriodicPattern(("1",), "full").validate_still_life())


class EnumeratorTests(unittest.TestCase):
    def test_encoding_is_deterministic(self):
        pattern = PeriodicPattern(("11..", "11..", "....", "...."))
        first = build_encoding(pattern, Window(0, 0, 3, 3), 1)
        second = build_encoding(pattern, Window(0, 0, 3, 3), 1)
        self.assertEqual(first.digest(), second.digest())

    def test_finds_and_independently_verifies_minimum(self):
        pattern = PeriodicPattern(("11..", "11..", "....", "...."), "block")
        result = enumerate_margins(pattern, Window(0, 0, 4, 4), 2)
        self.assertIsNotNone(result["minimum_margin"])
        self.assertEqual(
            [entry["status"] for entry in result["outcomes"][:-1]],
            ["UNSAT"] * result["minimum_margin"],
        )
        self.assertEqual(verify_witness(result["witness"]), [])

    def test_verifier_rejects_corruption(self):
        pattern = PeriodicPattern(("11..", "11..", "....", "...."), "block")
        witness = enumerate_margins(pattern, Window(0, 0, 2, 2), 1)["witness"]
        damaged = copy.deepcopy(witness)
        damaged["live_cells"].pop()
        self.assertTrue(verify_witness(damaged))

    def test_reports_finite_unsat_lower_bound(self):
        pattern = PeriodicPattern(("11..", "11..", "....", "...."), "block")
        result = enumerate_margins(pattern, Window(0, 0, 3, 1), 0)
        self.assertIsNone(result["witness"])
        self.assertEqual(result["lower_bound"], 1)
        self.assertEqual(result["outcomes"][0]["status"], "UNSAT")

    def test_exact_controlled_margin_two(self):
        pattern = PeriodicPattern((".1...", "1.1..", ".1...", ".....", "....."), "tub")
        result = enumerate_margins(pattern, Window(0, 0, 10, 1), 2)
        self.assertEqual(result["minimum_margin"], 2)
        self.assertEqual([item["status"] for item in result["outcomes"]], ["UNSAT", "UNSAT", "SAT"])


if __name__ == "__main__":
    unittest.main()
