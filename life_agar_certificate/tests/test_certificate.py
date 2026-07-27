import copy
import sys
import unittest
from fractions import Fraction
from pathlib import Path

DIRECTORY = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(DIRECTORY))

from model import life_output
from verify import load_certificate, verify


class LifeRuleTests(unittest.TestCase):
    @staticmethod
    def mask(center, neighbors):
        positions = [0, 1, 2, 3, 5, 6, 7, 8]
        value = center << 4
        for position in positions[:neighbors]:
            value |= 1 << position
        return value

    def test_b3_s23_truth_table_by_neighbor_count(self):
        for center in (0, 1):
            for neighbors in range(9):
                expected = int(neighbors == 3 or (center == 1 and neighbors == 2))
                self.assertEqual(
                    life_output(self.mask(center, neighbors)),
                    expected,
                    (center, neighbors),
                )


class CertificateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.certificate = load_certificate(DIRECTORY / "certificate.json")

    def test_exact_certificate_and_optimality_witness(self):
        result = verify(self.certificate)
        self.assertEqual(result["patterns"], 512)
        self.assertEqual(Fraction(result["bound"]), Fraction(8, 13))
        self.assertEqual(result["minimum_slack"], "0")
        self.assertEqual(result["witness_support"], 57)

    def test_tampered_bound_is_rejected(self):
        certificate = copy.deepcopy(self.certificate)
        certificate["bound"] = "1/2"
        with self.assertRaises(AssertionError):
            verify(certificate)


if __name__ == "__main__":
    unittest.main()
