import csv
import gzip
import hashlib
import json
import subprocess
import tempfile
import unittest
from itertools import product
from pathlib import Path

from life_safety import (
    check_all_single_gliders,
    check_bounded_flip,
    enumerate_still_life_classes,
    enumerate_interacting_attacks,
    search_three_by_three_invariant,
    step,
)
from life_safety.candidates import (
    _enumerate_still_lives,
    canonical_pattern,
    exclude_still_life_classes,
)
from life_safety.gliders import DIRECTIONS, glider, simulate_collision
from life_safety.independent import dense_step
from life_safety.invariant import (
    PROTECTED_INDEX,
    REGION,
    decode_boundary,
    decode_region,
    verify_exclusion,
)
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


class BoundaryInvariantTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.results = (
            search_three_by_three_invariant(False),
            search_three_by_three_invariant(True),
        )

    def test_three_by_three_invariant_class_is_empty(self):
        expected_counts = {False: [56, 200], True: [172, 84]}
        for result in self.results:
            self.assertTrue(result.excluded)
            self.assertEqual(len(result.eliminations), 256)
            counts = [
                sum(
                    elimination.round == round_number
                    for elimination in result.eliminations
                )
                for round_number in range(2)
            ]
            self.assertEqual(counts, expected_counts[result.protected_value])
            self.assertTrue(verify_exclusion(result))

    def test_elimination_witnesses_replay_with_dense_simulator(self):
        region = set(REGION)
        for result in self.results:
            ranks = {
                elimination.region_state: elimination.round
                for elimination in result.eliminations
            }
            for elimination in result.eliminations:
                initial = decode_region(elimination.region_state) | decode_boundary(
                    elimination.boundary_state
                )
                successor = frozenset(dense_step(initial) & region)
                self.assertEqual(successor, decode_region(elimination.successor))
                successor_value = bool(
                    elimination.successor & (1 << PROTECTED_INDEX)
                )
                if successor_value == result.protected_value:
                    self.assertLess(
                        ranks[elimination.successor],
                        elimination.round,
                    )


class BoundaryMemoryTests(unittest.TestCase):
    def test_packed_ranked_witnesses_verify_exhaustively(self):
        with (HERE / "examples" / "boundary_memory_summary.json").open() as source:
            summary = json.load(source)
        self.assertEqual(summary["center_alive"]["states"], 1 << 24)
        self.assertEqual(summary["center_dead"]["states"], 1 << 24)
        with tempfile.TemporaryDirectory() as temporary:
            temporary_path = Path(temporary)
            output_path = temporary_path / "certificates"
            process = subprocess.run(
                [
                    "python3",
                    str(HERE / "generate_boundary_memory.py"),
                    "--output",
                    str(output_path),
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            self.assertIn("verified protected=1", process.stdout)
            self.assertIn("verified protected=0", process.stdout)
            for name, key in (("live", "center_alive"), ("dead", "center_dead")):
                compressed_path = output_path / f"boundary_memory_{name}.bin.gz"
                compressed = compressed_path.read_bytes()
                self.assertEqual(len(compressed), summary[key]["gzip_bytes"])
                self.assertEqual(
                    hashlib.sha256(compressed).hexdigest(),
                    summary[key]["gzip_sha256"],
                )
                raw = gzip.decompress(compressed)
                self.assertEqual(len(raw), summary[key]["raw_bytes"])
                self.assertEqual(
                    hashlib.sha256(raw).hexdigest(),
                    summary[key]["raw_sha256"],
                )


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


class StillLifeCandidateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.candidates = enumerate_still_life_classes()
        with (HERE / "examples" / "still_life_4x4_candidates.csv").open() as source:
            cls.candidate_rows = list(csv.DictReader(source))
        with (HERE / "examples" / "still_life_4x4_attacks.csv").open() as source:
            cls.attack_rows = list(csv.DictReader(source))

    def test_four_by_four_enumeration_is_exhaustive_up_to_symmetry(self):
        normalized = []
        cells = tuple((x, y) for y in range(4) for x in range(4))
        for mask in range(1, 1 << len(cells)):
            pattern = frozenset(
                cell
                for index, cell in enumerate(cells)
                if mask & (1 << index)
            )
            if min(x for x, _ in pattern) or min(y for _, y in pattern):
                continue
            if dense_step(pattern) == pattern:
                normalized.append(pattern)
        self.assertEqual(len(normalized), 39)
        independent_classes = {canonical_pattern(pattern) for pattern in normalized}
        self.assertEqual(len(independent_classes), 13)
        self.assertEqual(
            independent_classes,
            {tuple(sorted(candidate.pattern)) for candidate in self.candidates},
        )

    def test_record_checks_every_attack_for_every_candidate(self):
        rows_by_candidate = {
            candidate.identifier: [] for candidate in self.candidates
        }
        for row in self.attack_rows:
            rows_by_candidate[row["candidate"]].append(row)
        self.assertEqual(len(self.attack_rows), 2344)
        for candidate in self.candidates:
            recorded = {
                (row["direction"], int(row["phase"]), int(row["lane"]))
                for row in rows_by_candidate[candidate.identifier]
            }
            expected = {
                (attack.direction, attack.phase, attack.lane)
                for attack in enumerate_interacting_attacks(candidate.pattern)
            }
            self.assertEqual(recorded, expected)

    def test_every_candidate_has_a_certified_exclusion_witness(self):
        self.assertEqual(len(self.candidate_rows), 13)
        candidates = {
            candidate.identifier: candidate for candidate in self.candidates
        }
        for row in self.candidate_rows:
            self.assertEqual(row["excluded_by_certified_collision"], "True")
            candidate = candidates[row["candidate"]]
            key = (
                row["witness_direction"],
                int(row["witness_phase"]),
                int(row["witness_lane"]),
            )
            attack = next(
                attack
                for attack in enumerate_interacting_attacks(candidate.pattern)
                if (attack.direction, attack.phase, attack.lane) == key
            )
            collision = simulate_collision(candidate.pattern, attack, horizon=256)
            self.assertEqual(collision.outcome, "changed_periodic")
            self.assertEqual(
                collision.settled_generation,
                int(row["witness_settled_generation"]),
            )
        self.assertEqual(
            max(int(row["restored"]) for row in self.candidate_rows),
            4,
        )

    def test_row_transfer_enumerates_every_five_by_five_still_life(self):
        four_by_four = _enumerate_still_lives(4, 4)
        five_by_five = _enumerate_still_lives(5, 5)
        self.assertEqual(len(four_by_four), 83)
        self.assertEqual(len(five_by_five), 417)
        self.assertEqual(len(set(five_by_five)), len(five_by_five))
        for pattern in five_by_five:
            self.assertEqual(dense_step(pattern), pattern)
        classes = enumerate_still_life_classes(5, 5)
        self.assertEqual(len(classes), 38)

    def test_five_by_five_early_witnesses_are_certified(self):
        with (HERE / "examples" / "still_life_5x5_exclusion.csv").open() as source:
            rows = list(csv.DictReader(source))
        self.assertEqual(len(rows), 38)
        candidates = {
            candidate.identifier: candidate
            for candidate in enumerate_still_life_classes(5, 5)
        }
        for row in rows:
            self.assertEqual(row["excluded"], "True")
            candidate = candidates[row["candidate"]]
            key = (
                row["witness_direction"],
                int(row["witness_phase"]),
                int(row["witness_lane"]),
            )
            attacks = enumerate_interacting_attacks(candidate.pattern)
            self.assertEqual(len(attacks), int(row["attack_count"]))
            attack = next(
                attack
                for attack in attacks
                if (attack.direction, attack.phase, attack.lane) == key
            )
            collision = simulate_collision(candidate.pattern, attack, horizon=512)
            self.assertEqual(collision.outcome, "changed_periodic")
            self.assertEqual(
                collision.settled_generation,
                int(row["witness_settled_generation"]),
            )
        exclusions = exclude_still_life_classes()
        self.assertTrue(all(exclusion.witness for exclusion in exclusions))


if __name__ == "__main__":
    unittest.main()
