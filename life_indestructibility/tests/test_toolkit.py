import csv
import json
import unittest
from itertools import product
from pathlib import Path

from life_safety import (
    check_all_single_gliders,
    check_bounded_flip,
    enumerate_interacting_attacks,
    step,
)
from life_safety.gliders import DIRECTIONS, glider
from life_safety.independent import dense_step
from life_safety.life import bounding_box, translate

HERE = Path(__file__).parent.parent
BLOCK = frozenset({(0, 0), (1, 0), (0, 1), (1, 1)})


def touches(first, second):
    return any(
        abs(ax - bx) <= 1 and abs(ay - by) <= 1
        for ax, ay in first
        for bx, by in second
    )


def independent_lane_hits(direction, phase, lane):
    dx, dy = DIRECTIONS[direction]
    tx, ty = 0, lane // dx
    moving = translate(glider(direction, phase), tx, ty)
    while not (
        (dx > 0 and max(x for x, _ in moving) < -6)
        or (dx < 0 and min(x for x, _ in moving) > 7)
    ):
        moving = translate(moving, -4 * dx, -4 * dy)
    for _ in range(80):
        if touches(moving, BLOCK):
            return True
        moving = dense_step(moving)
        xmin, xmax, ymin, ymax = bounding_box(moving)
        if (
            (dx > 0 and xmin > 3)
            or (dx < 0 and xmax < -2)
            or (dy > 0 and ymin > 3)
            or (dy < 0 and ymax < -2)
        ):
            return False
    raise AssertionError("independent glider did not pass target")


class LifeTests(unittest.TestCase):
    def test_sparse_step_matches_independent_dense_implementation(self):
        patterns = [
            BLOCK,
            glider("SE", 0),
            frozenset({(-2, 1), (0, 0), (1, 0), (1, 1), (3, -1)}),
        ]
        for pattern in patterns:
            for _ in range(12):
                self.assertEqual(step(pattern), dense_step(pattern))
                pattern = step(pattern)

    def test_glider_directions_and_phases(self):
        for direction, displacement in DIRECTIONS.items():
            initial = glider(direction, 0)
            after_four = initial
            for _ in range(4):
                after_four = dense_step(after_four)
            self.assertEqual(after_four, translate(initial, *displacement))
            for phase in range(4):
                self.assertEqual(len(glider(direction, phase)), 5)


class BoundedTests(unittest.TestCase):
    def test_one_tick_universal_safe_case(self):
        target = frozenset({(-1, 0), (0, 0), (1, 0)})
        result = check_bounded_flip(target, (-1, 1, -1, 1), (0, 0), 1)
        self.assertTrue(result.safe)

    def test_sat_counterexample_replays_independently(self):
        result = check_bounded_flip(BLOCK, (0, 1, 0, 1), (0, 0), 1)
        self.assertFalse(result.safe)
        self.assertEqual(result.flip_generation, 1)
        self.assertEqual(dense_step(result.trace[0]), result.trace[1])
        self.assertNotIn((0, 0), result.trace[1])

    def test_sat_answer_matches_brute_force(self):
        cases = [
            (frozenset(), (0, 0, 0, 0)),
            (frozenset({(0, 0)}), (0, 0, 0, 0)),
            (BLOCK, (0, 1, 0, 1)),
            (frozenset({(-1, 0), (0, 0), (1, 0)}), (-1, 1, -1, 1)),
        ]
        neighborhood = {
            (x, y) for x in range(-1, 2) for y in range(-1, 2)
        }
        for target, bounds in cases:
            inside = {
                (x, y)
                for x in range(bounds[0], bounds[1] + 1)
                for y in range(bounds[2], bounds[3] + 1)
            }
            exterior = sorted(neighborhood - inside)
            brute_flip = False
            for values in product((False, True), repeat=len(exterior)):
                initial = target | frozenset(
                    cell for cell, value in zip(exterior, values) if value
                )
                if ((0, 0) in dense_step(initial)) != ((0, 0) in target):
                    brute_flip = True
                    break
            result = check_bounded_flip(target, bounds, (0, 0), 1)
            self.assertEqual(result.safe, not brute_flip)


class GliderEnumerationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.attacks = enumerate_interacting_attacks(BLOCK)
        cls.results = check_all_single_gliders(BLOCK, collision_horizon=128)

    def test_all_direction_phase_lane_classes_are_unique_and_complete(self):
        keys = {
            (attack.direction, attack.phase, attack.lane)
            for attack in self.attacks
        }
        self.assertEqual(len(keys), len(self.attacks))
        for direction in DIRECTIONS:
            for phase in range(4):
                actual = {
                    lane
                    for attack_direction, attack_phase, lane in keys
                    if (attack_direction, attack_phase) == (direction, phase)
                }
                expected = {
                    lane
                    for lane in range(-20, 21)
                    if independent_lane_hits(direction, phase, lane)
                }
                self.assertEqual(actual, expected)

    def test_large_target_lane_after_generation_64_is_not_missed(self):
        far_block = translate(BLOCK, 20, 0)
        target = BLOCK | far_block
        attacks = enumerate_interacting_attacks(target)
        attack = next(
            attack
            for attack in attacks
            if (attack.direction, attack.phase, attack.lane) == ("SE", 0, -25)
        )
        moving = attack.initial_glider
        first_touch = None
        for generation in range(200):
            if touches(moving, target):
                first_touch = generation
                break
            moving = dense_step(moving)
        self.assertIsNotNone(first_touch)
        self.assertGreater(first_touch, 64)

    def test_collision_traces_replay_with_independent_simulator(self):
        for result in self.results:
            for before, after in zip(result.trace, result.trace[1:]):
                self.assertEqual(dense_step(before), after)
            if result.outcome == "changed_periodic":
                self.assertIsNotNone(result.settled_period)
            elif result.outcome == "unresolved_by_horizon":
                self.assertIsNone(result.settled_generation)

    def test_checked_csv_contains_every_enumerated_attack(self):
        with (HERE / "examples" / "block_single_gliders.csv").open() as source:
            rows = list(csv.DictReader(source))
        csv_keys = {
            (row["direction"], int(row["phase"]), int(row["lane"]))
            for row in rows
        }
        attack_keys = {
            (attack.direction, attack.phase, attack.lane)
            for attack in self.attacks
        }
        self.assertEqual(csv_keys, attack_keys)
        self.assertEqual(len(rows), len(self.results))

    def test_checked_counterexample_has_certified_settling(self):
        with (
            HERE / "examples" / "block_collision_counterexample.json"
        ).open() as source:
            example = json.load(source)
        self.assertEqual(example["outcome"], "changed_periodic")
        self.assertGreaterEqual(example["settled_period"], 1)
        self.assertNotEqual(
            {tuple(cell) for cell in example["final"]},
            BLOCK,
        )


if __name__ == "__main__":
    unittest.main()
