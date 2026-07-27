import copy
import unittest

from life_density.verify import least_temporal_period, step, verify_result


def result_for(phases, *, exact_period):
    height = len(phases[0])
    width = len(phases[0][0])
    period = len(phases)
    total = sum(row.count("O") for phase in phases for row in phase)
    return {
        "schema": "life-density/v1",
        "status": "feasible",
        "parameters": {
            "width": width,
            "height": height,
            "period": period,
            "exact_period": exact_period,
            "topology": "torus_directional_moore",
            "rule": "B3/S23",
        },
        "objective": {
            "total_live": total,
            "spacetime_cells": width * height * period,
            "density": {
                "numerator": total,
                "denominator": width * height * period,
            },
        },
        "witness": {"phases": phases},
    }


class SimulationTests(unittest.TestCase):
    def test_block_is_still_life(self):
        block = [
            ".....",
            ".OO..",
            ".OO..",
            ".....",
            ".....",
        ]
        self.assertEqual(step([[c == "O" for c in row] for row in block]), [
            [c == "O" for c in row] for row in block
        ])
        report = verify_result(result_for([block], exact_period=True))
        self.assertTrue(report["valid"], report)
        self.assertEqual(report["least_period"], 1)

    def test_blinker_has_exact_period_two(self):
        horizontal = [
            ".....",
            ".....",
            ".OOO.",
            ".....",
            ".....",
        ]
        vertical = [
            ".....",
            "..O..",
            "..O..",
            "..O..",
            ".....",
        ]
        report = verify_result(result_for([horizontal, vertical], exact_period=True))
        self.assertTrue(report["valid"], report)
        parsed = [
            [[cell == "O" for cell in row] for row in phase]
            for phase in [horizontal, vertical]
        ]
        self.assertEqual(least_temporal_period(parsed), 2)

    def test_exact_period_rejects_repeated_still_life(self):
        block = [
            ".....",
            ".OO..",
            ".OO..",
            ".....",
            ".....",
        ]
        report = verify_result(result_for([block, block], exact_period=True))
        self.assertFalse(report["valid"])
        self.assertEqual(report["least_period"], 1)

    def test_corrupt_transition_is_rejected(self):
        horizontal = [".....", ".....", ".OOO.", ".....", "....."]
        corrupt = copy.deepcopy(horizontal)
        corrupt[0] = "O...."
        report = verify_result(result_for([horizontal, corrupt], exact_period=False))
        self.assertFalse(report["valid"])
        self.assertTrue(any("transition" in error for error in report["errors"]))


if __name__ == "__main__":
    unittest.main()

