import json
import unittest
from pathlib import Path

from elementary_replicator.branching_certificate import (
    generate_certificate,
    verify_certificate,
)
from elementary_replicator.theorem import (
    first_phased_capacity_contradiction,
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


if __name__ == "__main__":
    unittest.main()
