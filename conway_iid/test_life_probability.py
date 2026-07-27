import itertools
import math
import pathlib
import shutil
import subprocess
import tempfile
import unittest
from fractions import Fraction

from life_probability import (
    bernstein_to_power,
    exact_probability,
    evaluate_power,
    monte_carlo,
)
from verify_protected_blinker import (
    cylinder_exponent,
    cylinder_probability,
    verify_horizon,
)


TIME_TWO_COUNTS = [
    0,
    0,
    0,
    22,
    1092,
    10902,
    52808,
    159532,
    352308,
    662834,
    1136852,
    1653846,
    1844296,
    1487120,
    813480,
    273548,
    49756,
    3962,
    72,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
]


def direct_time_one_counts():
    counts = [0] * 10
    for bits in itertools.product((False, True), repeat=9):
        center = bits[4]
        neighbor_count = sum(bits) - center
        if neighbor_count == 3 or (center and neighbor_count == 2):
            counts[sum(bits)] += 1
    return counts


class ExactProbabilityTests(unittest.TestCase):
    def test_time_zero(self):
        result = exact_probability(0)
        self.assertEqual(result["weight_counts"], [0, 1])
        self.assertEqual(result["power_coefficients"], [0, 1])

    def test_time_one_against_direct_exhaustion(self):
        result = exact_probability(1)
        self.assertEqual(result["weight_counts"], direct_time_one_counts())
        self.assertEqual(
            result["power_coefficients"],
            [0, 0, 0, 84, -448, 980, -1120, 700, -224, 28],
        )

    def test_time_two_known_exact_counts_and_power_conversion(self):
        result = exact_probability(2)
        self.assertEqual(result["weight_counts"], TIME_TWO_COUNTS)
        self.assertEqual(
            result["power_coefficients"],
            bernstein_to_power(TIME_TWO_COUNTS),
        )
        self.assertEqual(sum(TIME_TWO_COUNTS), 8502430)

    @unittest.skipUnless(shutil.which("cc"), "a C compiler is required")
    def test_time_two_against_independent_full_exhaustion(self):
        source = pathlib.Path(__file__).with_name("exhaustive_t2.c")
        with tempfile.TemporaryDirectory() as directory:
            executable = pathlib.Path(directory) / "exhaustive_t2"
            subprocess.run(
                ["cc", "-O3", str(source), "-o", str(executable)],
                check=True,
            )
            output = subprocess.run(
                [str(executable)],
                check=True,
                capture_output=True,
                text=True,
            ).stdout
        self.assertEqual([int(value) for value in output.split()], TIME_TWO_COUNTS)

    def test_monte_carlo_at_selected_probabilities(self):
        coefficients = exact_probability(2)["power_coefficients"]
        trials = 30_000
        for seed, p in enumerate((0.1, 0.3, 0.5), start=10):
            exact = evaluate_power(coefficients, p)
            estimate = monte_carlo(2, p, trials, seed)
            standard_error = math.sqrt(exact * (1 - exact) / trials)
            self.assertLess(abs(estimate - exact), 6 * standard_error + 0.001)

    def test_monte_carlo_rejects_nonpositive_trial_counts(self):
        for trials in (0, -1):
            with self.subTest(trials=trials):
                with self.assertRaisesRegex(
                    ValueError, "trials must be a positive integer"
                ):
                    monte_carlo(2, 0.3, trials, 1)

    def test_monte_carlo_rejects_boolean_trial_count(self):
        with self.assertRaisesRegex(ValueError, "trials must be a positive integer"):
            monte_carlo(2, 0.3, True, 1)

    def test_rejects_unsupported_time(self):
        with self.assertRaisesRegex(ValueError, "limited"):
            exact_probability(3)


class ProtectedBlinkerTests(unittest.TestCase):
    def test_protected_blinker_across_horizons(self):
        for horizon in range(21):
            verify_horizon(horizon)

    def test_cylinder_exponent_and_probability(self):
        self.assertEqual(
            [cylinder_exponent(horizon) for horizon in range(4)],
            [22, 46, 78, 118],
        )
        p = Fraction(1, 4)
        for horizon in range(4):
            expected = p**3 * (1 - p) ** ((2 * (horizon + 2) + 1) ** 2 - 3)
            self.assertEqual(cylinder_probability(horizon, p), expected)


if __name__ == "__main__":
    unittest.main()
