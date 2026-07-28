import json
import unittest
from pathlib import Path

from elementary_replicator.branching_certificate import (
    generate_certificate,
    verify_certificate,
)
from elementary_replicator.theorem import (
    first_phased_capacity_contradiction,
    forced_lineage_cancellations,
    light_cone_capacity,
    minimum_elapsed_time_for_copies,
    phase_counts,
    phased_capacity_at_generation,
)


CERTIFICATE = (
    Path(__file__).parents[1]
    / "certificates"
    / "two_phase_fibonacci.json"
)


class BranchingObstructionTests(unittest.TestCase):
    def test_reflection_phase_counts_follow_fibonacci_substitution(self):
        substitution = ((0, 1), (1, 1))
        self.assertEqual(phase_counts(substitution, 0, 0), (1, 0))
        self.assertEqual(phase_counts(substitution, 0, 8), (13, 21))

    def test_certificate_is_first_capacity_contradiction(self):
        certificate = json.loads(CERTIFICATE.read_text())
        self.assertTrue(verify_certificate(certificate))
        generation = certificate["generation"]
        previous = phased_capacity_at_generation(
            certificate["substitution"],
            certificate["initial_phase"],
            certificate["minimum_phase_population"],
            certificate["width"],
            certificate["height"],
            certificate["period"],
            generation - 1,
            certificate["radius"],
        )
        self.assertLessEqual(previous[1], previous[2])
        self.assertGreater(
            certificate["required_cells"],
            certificate["available_cells"],
        )

    def test_phase_changing_binary_branching_is_also_excluded(self):
        substitution = ((0, 2), (2, 0))
        generation = first_phased_capacity_contradiction(
            substitution, 0, 1, 1, 1, 1
        )
        counts, required, available = phased_capacity_at_generation(
            substitution, 0, 1, 1, 1, 1, generation
        )
        self.assertEqual(sum(counts), 1 << generation)
        self.assertGreater(required, available)

    def test_tampered_certificate_fails(self):
        certificate = generate_certificate(
            [[0, 1], [1, 1]], 0, 1, 1, 1, 1
        )
        certificate["required_cells"] += 1
        self.assertFalse(verify_certificate(certificate))

    def test_minimum_time_is_exact_for_polynomial_copy_growth(self):
        copies = 10_000
        elapsed = minimum_elapsed_time_for_copies(1, 1, copies)
        self.assertEqual(elapsed, 50)
        self.assertGreaterEqual(light_cone_capacity(1, 1, elapsed), copies)
        self.assertLess(light_cone_capacity(1, 1, elapsed - 1), copies)

    def test_exponential_lineages_force_asymptotic_cancellation(self):
        nominal = 1 << 30
        cancelled = forced_lineage_cancellations(
            nominal, 4, width=1, height=1, elapsed=30
        )
        self.assertEqual(cancelled, nominal - 4 * 61 * 61)
        self.assertGreater(cancelled * 100, nominal * 99)

    def test_unbounded_coalescence_is_the_only_no_cancellation_escape(self):
        nominal = 1 << 20
        capacity = light_cone_capacity(1, 1, 20)
        minimum_load = (nominal + capacity - 1) // capacity
        self.assertGreater(
            forced_lineage_cancellations(
                nominal, minimum_load - 1, 1, 1, 20
            ),
            0,
        )
        self.assertEqual(
            forced_lineage_cancellations(
                nominal, minimum_load, 1, 1, 20
            ),
            0,
        )

    def test_invalid_escape_hatch_arguments_fail(self):
        with self.assertRaises(ValueError):
            minimum_elapsed_time_for_copies(1, 1, 1, radius=0)
        with self.assertRaises(ValueError):
            forced_lineage_cancellations(0, 1, 1, 1, 1)


if __name__ == "__main__":
    unittest.main()
