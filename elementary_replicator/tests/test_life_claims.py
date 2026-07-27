import unittest

from elementary_replicator.life import evolve, reflect_y, translate
from elementary_replicator.theorem import (
    capacity_at_generation,
    first_capacity_contradiction,
)

PRE_PULSAR = frozenset(
    {
        (1, 0), (7, 0),
        (0, 1), (1, 1), (2, 1),
        (6, 1), (7, 1), (8, 1),
    }
)
PI = frozenset(
    {
        (0, 0), (1, 0), (2, 0),
        (0, 1), (2, 1),
        (0, 2), (2, 2),
    }
)


class LifeClaimsTests(unittest.TestCase):
    def test_pre_pulsar_first_event_and_failed_recurrence(self):
        generation_15 = evolve(PRE_PULSAR, 15)
        top = translate(PRE_PULSAR, (0, -3))
        bottom = translate(reflect_y(PRE_PULSAR), (0, 5))
        self.assertEqual(generation_15, top | bottom)

        together = evolve(generation_15, 15)
        separately = evolve(top, 15) | evolve(bottom, 15)
        self.assertEqual((len(together), len(separately)), (48, 26))
        self.assertEqual(len(together ^ separately), 42)

    def test_pi_has_two_copies_and_immediate_debris_interference(self):
        generation_26 = evolve(PI, 26)
        copies = translate(PI, (0, -8)) | translate(PI, (0, -2))
        self.assertTrue(copies <= generation_26)
        self.assertEqual((len(generation_26), len(generation_26 - copies)), (67, 53))
        self.assertNotEqual(evolve(generation_26, 1), evolve(copies, 1))

    def test_fixed_period_binary_branching_hits_capacity_contradiction(self):
        generation = first_capacity_contradiction(9, 2, 8, 15)
        required, available = capacity_at_generation(9, 2, 8, 15, generation)
        self.assertGreater(required, available)
        previous = capacity_at_generation(9, 2, 8, 15, generation - 1)
        self.assertLessEqual(*previous)


if __name__ == "__main__":
    unittest.main()
