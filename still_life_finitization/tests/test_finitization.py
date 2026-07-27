import copy
import itertools
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from still_life_finitization.still_life.pattern import PeriodicPattern, Window
from still_life_finitization.still_life.sat import build_encoding, enumerate_margins
from still_life_finitization.still_life.stripe_transfer import (
    COLUMN_STRIPE_PATTERN,
    MARGIN as STRIPE_MARGIN,
    STRIPE_PATTERN,
    StripeSeed,
    construct_columns_from_seeds,
    construct_from_seeds,
    pump_horizontal,
    pump_vertical,
    verify_stripe_certificate,
)
from still_life_finitization.still_life.transfer import (
    RectangleTransferAutomaton,
    analyze_component_agar,
    block_agar,
    verify_transfer_certificate,
)
from still_life_finitization.still_life.verify import verify_witness
from still_life_finitization.still_life.verify import verify_cells


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


class TransferTheoremTests(unittest.TestCase):
    def test_checked_certificate_recomputes_exactly(self):
        certificate_path = (
            Path(__file__).resolve().parents[1]
            / "automata"
            / "block_4x4_certificate.json"
        )
        certificate = json.loads(certificate_path.read_text())
        self.assertEqual(verify_transfer_certificate(certificate), [])
        self.assertEqual(certificate, analyze_component_agar(block_agar()))
        self.assertEqual(certificate["state_count"], 256)
        self.assertEqual(certificate["uniform_margin_bound"], 1)

    def test_transfer_reaches_every_rectangle_state(self):
        automaton = RectangleTransferAutomaton(4, 4)
        for x, y, width, height in itertools.product(
            range(-4, 5), range(-4, 5), range(1, 10), range(1, 10)
        ):
            window = Window(x, y, width, height)
            state = (x % 4, x % 4, y % 4, y % 4)
            for _ in range(width - 1):
                state = automaton.transition(state, "E")
            for _ in range(height - 1):
                state = automaton.transition(state, "S")
            self.assertEqual(state, automaton.state(window))

    def test_parametric_block_family_all_phases_and_two_periods(self):
        for period_x, period_y in ((4, 4), (4, 7), (5, 6), (8, 4)):
            agar = block_agar(period_x, period_y)
            self.assertEqual(agar.validate_components(), [])
            for x, y, width, height in itertools.product(
                range(period_x),
                range(period_y),
                range(1, 2 * period_x + 1),
                range(1, 2 * period_y + 1),
            ):
                self.assertEqual(agar.verify_window(Window(x, y, width, height)), [])

    def test_uniform_bound_one_is_sharp(self):
        result = enumerate_margins(block_agar().pattern(), Window(0, 0, 1, 1), 1)
        self.assertEqual(result["minimum_margin"], 1)
        self.assertEqual(
            [outcome["status"] for outcome in result["outcomes"]],
            ["UNSAT", "SAT"],
        )

    def test_tampered_transfer_certificate_is_rejected(self):
        certificate = analyze_component_agar(block_agar())
        certificate["uniform_margin_bound"] = 0
        self.assertEqual(
            verify_transfer_certificate(certificate),
            ["certificate does not match the recomputed transfer analysis"],
        )


class AdversarialSearchTests(unittest.TestCase):
    def test_checked_adversarial_bounds_and_witnesses(self):
        result_path = (
            Path(__file__).resolve().parents[1]
            / "experiments"
            / "adversarial_results.json"
        )
        result = json.loads(result_path.read_text())
        self.assertEqual(result["case_count"], len(result["cases"]))
        self.assertEqual(result["case_count"], 80)
        for case in result["cases"]:
            self.assertEqual(verify_witness(case["witness"]), [])
            minimum = case["minimum_margin"]
            self.assertEqual(
                [outcome["status"] for outcome in case["outcomes"]],
                ["UNSAT"] * minimum + ["SAT"],
            )
        stripes = [
            case["minimum_margin"]
            for case in result["cases"]
            if case["family"] == "alternating-live-rows-height-1"
        ]
        self.assertEqual(stripes, [1, 1, 2, 2] + [3] * 28)


class AlternatingRowTheoremTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        certificate_path = (
            Path(__file__).resolve().parents[1]
            / "automata"
            / "alternating_rows_certificate.json"
        )
        cls.certificate = json.loads(certificate_path.read_text())
        cls.seeds = {
            (
                data["window"]["y"],
                data["window"]["width"],
                data["window"]["height"],
            ): StripeSeed.from_dict(data)
            for data in cls.certificate["seeds"]
        }

    def test_exact_certificate_verifies(self):
        self.assertEqual(verify_stripe_certificate(self.certificate), [])
        self.assertEqual(self.certificate["summary"]["seed_count"], 264)
        self.assertEqual(self.certificate["summary"]["margin_bound"], 3)

    def test_pumps_commute_and_preserve_still_life_repeatedly(self):
        seed = self.seeds[(0, 9, 9)]
        first = pump_vertical(pump_horizontal(seed, 3), 2)
        second = pump_horizontal(pump_vertical(seed, 2), 3)
        self.assertEqual(first, second)
        self.assertEqual(
            verify_cells(
                STRIPE_PATTERN,
                first.window,
                STRIPE_MARGIN,
                set(first.live_cells),
            ),
            [],
        )

    def test_constructs_all_phase_and_residue_classes(self):
        dimensions = (
            list(range(1, 18))
            + [23, 31, 44, 57]
        )
        for x, y, width, height in itertools.product(
            (-7, 0, 13), (-8, -7, 0, 1), dimensions, dimensions
        ):
            window = Window(x, y, width, height)
            live_cells = construct_from_seeds(window, self.seeds)
            self.assertEqual(
                verify_cells(STRIPE_PATTERN, window, 3, live_cells),
                [],
                (x, y, width, height),
            )

    def test_rotates_to_all_column_phases(self):
        for x, y, width, height in itertools.product(
            (-3, -2, 0, 1), (-5, 0, 8), (1, 5, 9, 17, 26), (1, 4, 10, 23)
        ):
            window = Window(x, y, width, height)
            live_cells = construct_columns_from_seeds(window, self.seeds)
            self.assertEqual(
                verify_cells(COLUMN_STRIPE_PATTERN, window, 3, live_cells),
                [],
                (x, y, width, height),
            )

    def test_tampered_stripe_certificate_is_rejected(self):
        damaged = copy.deepcopy(self.certificate)
        damaged["seeds"][0]["live_cells"].append([100, 100])
        errors = verify_stripe_certificate(damaged)
        self.assertEqual(errors, ["seed digest does not match"])


if __name__ == "__main__":
    unittest.main()
