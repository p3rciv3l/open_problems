import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from still_life_finitization.still_life.pattern import PeriodicPattern, Window
from still_life_finitization.still_life.sat import build_encoding, enumerate_margins
from still_life_finitization.still_life.verify import verify_witness


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


class VerifierValidationTests(unittest.TestCase):
    def setUp(self):
        self.witness = {
            "pattern": {"name": "dead", "rows": ["."]},
            "window": {"x": 0, "y": 0, "width": 1, "height": 1},
            "margin": 0,
            "live_cells": [],
        }

    def test_missing_fields_have_deterministic_errors(self):
        expected = [
            "missing field: pattern",
            "missing field: window",
            "missing field: margin",
            "missing field: live_cells",
        ]
        self.assertEqual(verify_witness({}), expected)
        self.assertEqual(verify_witness({}), expected)

    def test_wrong_top_level_type_is_an_error(self):
        self.assertEqual(verify_witness(None), ["witness must be an object"])

    def test_wrong_nested_types_are_errors(self):
        cases = [
            ("pattern", [], ["pattern must be an object"]),
            ("window", [], ["window must be an object"]),
            ("margin", "0", ["margin must be a nonnegative integer"]),
            ("live_cells", {}, ["live_cells must be an array"]),
        ]
        for field, value, expected in cases:
            with self.subTest(field=field):
                damaged = copy.deepcopy(self.witness)
                damaged[field] = value
                self.assertEqual(verify_witness(damaged), expected)

    def test_malformed_and_nonnumeric_coordinates_are_errors(self):
        self.witness["live_cells"] = [[1], [1, 2, 3], "1,2", [1, "x"], [True, 2]]
        self.assertEqual(
            verify_witness(self.witness),
            [
                "live_cells[0] must be a coordinate pair",
                "live_cells[1] must be a coordinate pair",
                "live_cells[2] must be a coordinate pair",
                "live_cells[3] coordinates must be integers",
                "live_cells[4] coordinates must be integers",
            ],
        )

    def test_nonnumeric_window_values_are_errors(self):
        self.witness["window"] = {"x": "zero", "y": None, "width": 1.5, "height": True}
        self.assertEqual(
            verify_witness(self.witness),
            [
                "window.x must be an integer",
                "window.y must be an integer",
                "window.width must be an integer",
                "window.height must be an integer",
            ],
        )


class ReproductionCommandTests(unittest.TestCase):
    def test_experiment_module_invocation_from_repository_root(self):
        repository = Path(__file__).resolve().parents[2]
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory, "result.json")
            completed = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "still_life_finitization.experiments.run_experiments",
                    "--max-cases",
                    "1",
                    "--output",
                    str(output),
                ],
                cwd=repository,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            result = json.loads(output.read_text())
            self.assertEqual(result["case_count"], 1)
            self.assertEqual(result["cases"][0]["family"], "block-aligned-squares")


if __name__ == "__main__":
    unittest.main()
