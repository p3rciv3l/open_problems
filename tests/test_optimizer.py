import unittest

from life_density.optimizer import optimize
from life_density.verify import verify_result


class OptimizerTests(unittest.TestCase):
    def test_finds_small_still_life_optimum(self):
        result = optimize(3, 3, 1)
        self.assertEqual(result["status"], "optimal")
        self.assertEqual(result["bounds"]["lower"], result["bounds"]["upper"])
        self.assertTrue(verify_result(result)["valid"])

    def test_exact_period_two_excludes_fixed_points(self):
        result = optimize(4, 4, 2, exact_period=True)
        self.assertEqual(result["status"], "optimal")
        self.assertEqual(result["verification"]["least_period"], 2)
        self.assertTrue(verify_result(result)["valid"])

    def test_exact_period_can_be_infeasible(self):
        result = optimize(1, 1, 2, exact_period=True)
        self.assertEqual(result["status"], "unsat")


if __name__ == "__main__":
    unittest.main()
