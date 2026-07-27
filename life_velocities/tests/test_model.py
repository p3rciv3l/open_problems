import unittest

import z3

from life_velocities.model import SearchSpec, WaveModel
from life_velocities.simulate import verify_witness


class ModelTests(unittest.TestCase):
    @staticmethod
    def _force_stationary_block(model):
        for variable in model.background.values():
            model.solver.add(z3.Not(variable))
        for t, x, y in model.representatives.values():
            model.solver.add(
                model.cell(t, x, y)
                == ((x % 4, y % 4) in {(1, 1), (1, 2), (2, 1), (2, 2)})
            )

    def test_life_rule_truth_table(self):
        current = z3.Bool("current")
        following = z3.Bool("following")
        neighbors = [z3.Bool(f"n{i}") for i in range(8)]
        for alive in (False, True):
            for count in range(9):
                solver = z3.Solver()
                solver.add(WaveModel._life_rule(following, current, neighbors))
                solver.add(current == alive)
                solver.add(following == (count == 3 or (alive and count == 2)))
                solver.add([neighbor == (i < count) for i, neighbor in enumerate(neighbors)])
                self.assertEqual(solver.check(), z3.sat)

    def test_small_exact_unsat_is_serializable(self):
        spec = SearchSpec(
            length=3,
            width=1,
            period=1,
            displacement=0,
            background_x_period=1,
            background_y_period=1,
            guard_columns=1,
            require_live_background=True,
        )
        result = WaveModel(spec).solve()
        self.assertEqual(result["status"], "unsat")
        self.assertNotIn("live_cosets", result)

    def test_independent_simulator_accepts_sat_witness(self):
        spec = SearchSpec(
            length=4,
            width=4,
            period=1,
            displacement=0,
            background_x_period=4,
            background_y_period=4,
            guard_columns=1,
            require_live_background=False,
            require_motion=False,
        )
        model = WaveModel(spec)
        self._force_stationary_block(model)
        result = model.solve()
        self.assertEqual(result["status"], "sat")
        self.assertEqual(verify_witness(result), [])

    def test_encoder_rejects_stationary_witness_when_motion_required(self):
        spec = SearchSpec(
            length=4,
            width=4,
            period=1,
            displacement=0,
            background_x_period=4,
            background_y_period=4,
            guard_columns=1,
            require_live_background=False,
            require_motion=True,
        )
        model = WaveModel(spec)
        self._force_stationary_block(model)
        self.assertEqual(model.solve()["status"], "unsat")

    def test_verifier_rejects_stationary_witness_when_motion_required(self):
        spec = SearchSpec(
            length=4,
            width=4,
            period=1,
            displacement=0,
            background_x_period=4,
            background_y_period=4,
            guard_columns=1,
            require_live_background=False,
            require_motion=False,
        )
        model = WaveModel(spec)
        self._force_stationary_block(model)
        result = model.solve()
        self.assertEqual(result["status"], "sat")
        result["spec"]["require_motion"] = True
        self.assertEqual(
            verify_witness(result),
            ["witness is stationary over the required period"],
        )


if __name__ == "__main__":
    unittest.main()
