import copy
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from fractions import Fraction
from pathlib import Path

DIRECTORY = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(DIRECTORY))

from entropy_obstruction import analyze as analyze_entropy_obstruction
from model import life_output
from pyramid_obstruction import analyze as analyze_pyramid_obstruction
from spectral_identities import verify_all as verify_spectral_identities
from strip2_verify import load_certificate as load_strip2_certificate
from strip2_verify import verify as verify_strip2
from temporal_charging_obstruction import (
    step,
    verify_all_long_prefixes_3x3,
    verify_survivor_stability_obstruction,
)
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

    def test_minimal_temporal_charging_obstructions(self):
        self.assertEqual(step(0b000_000_111, 3, 3), 0b111_111_111)
        self.assertEqual(step(0b111_111_111, 3, 3), 0)
        stability = verify_survivor_stability_obstruction()
        self.assertEqual(stability["states"], 512)
        self.assertEqual(
            Fraction(stability["maximum_birth_to_survivor_deficit_ratio"]), 4
        )
        verify_all_long_prefixes_3x3()
        self.assertEqual(step(0x557, 4, 3), 0x555)
        self.assertEqual(step(0x555, 4, 3), 0x555)

    def test_exact_polynomial_and_spectral_identities(self):
        report = verify_spectral_identities()
        self.assertEqual(report["degree_constrained_4x3_states"], 1132)
        self.assertEqual(
            Fraction(report["maximum_degree_constrained_4x3_density"]),
            Fraction(1, 2),
        )
        self.assertEqual(report["3x3_cycles"], 127)


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


class EntropyObstructionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = analyze_entropy_obstruction(DIRECTORY)

    def test_locally_stationary_witness_exceeds_one_half(self):
        self.assertEqual(
            Fraction(self.report["local_witness_density"]), Fraction(8, 13)
        )
        self.assertEqual(self.report["local_witness_support"], 57)

    def test_noninteracting_blinker_product(self):
        self.assertEqual(self.report["blinker_spacing"], 5)
        self.assertEqual(self.report["blinker_labelings_checked"], 81)
        self.assertEqual(self.report["blinker_density"], "3*q/25")
        self.assertEqual(self.report["blinker_activity"], "4*q/25")


class Strip2CertificateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.certificate = load_strip2_certificate(
            DIRECTORY / "strip2_certificate.json"
        )

    def test_exact_strip_certificate_and_lower_witness(self):
        result = verify_strip2(self.certificate)
        self.assertEqual(result["patterns"], 4096)
        self.assertEqual(
            Fraction(result["density_bound"]), Fraction(12001, 20000)
        )
        self.assertLess(Fraction(result["density_bound"]), Fraction(8, 13))
        self.assertEqual(
            Fraction(result["lp_density_lower_bound"]), Fraction(3, 5)
        )
        self.assertEqual(result["minimum_slack"], "0")
        self.assertEqual(result["witness_support"], 4)

    def test_tampered_strip_bound_is_rejected(self):
        certificate = copy.deepcopy(self.certificate)
        certificate["block_constant"] = "6/5"
        certificate["density_bound"] = "3/5"
        with self.assertRaises(AssertionError):
            verify_strip2(certificate)


class PyramidObstructionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = analyze_pyramid_obstruction(DIRECTORY)

    def test_stored_maximizers_are_extinction_transients(self):
        self.assertEqual(self.report["6x8"]["live_counts"], [44, 0, 0])
        self.assertEqual(self.report["6x10"]["live_counts"], [60, 0, 0])
        self.assertEqual(self.report["6x12"]["live_counts"], [68, 0, 0])
        self.assertEqual(self.report["6x8"]["score"], 174312)
        self.assertEqual(self.report["6x10"]["score"], 555788)
        self.assertEqual(self.report["6x12"]["score"], 555468)

    def test_dual_has_temporal_flux_but_large_spatial_seam_defect(self):
        dual = self.report["6x8"]["dual"]
        self.assertEqual(dual["support"], 19)
        for _, deaths, births in dual["expected_transitions"]:
            self.assertEqual(Fraction(deaths), Fraction(births))
        defects = {
            (entry["layer"], entry["axis"]): Fraction(entry["total_variation"])
            for entry in dual["overlap_defects"]
        }
        self.assertEqual(defects[(0, "x")], Fraction(73904, 78167))
        self.assertEqual(defects[(0, "y")], Fraction(63504, 78167))
        self.assertGreater(defects[(0, "x")], Fraction(9, 10))


@unittest.skipUnless(shutil.which("g++"), "g++ is required")
class PyramidCertificateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary_directory = tempfile.TemporaryDirectory()
        cls.executable = Path(cls.temporary_directory.name) / "pyramid_verify"
        cls.strong_executable = (
            Path(cls.temporary_directory.name) / "pyramid_6x8_verify"
        )
        cls.larger_executable = (
            Path(cls.temporary_directory.name) / "pyramid_6x10_verify"
        )
        cls.longer_executable = (
            Path(cls.temporary_directory.name) / "pyramid_6x12_verify"
        )
        subprocess.run(
            [
                "g++",
                "-O3",
                "-std=c++17",
                str(DIRECTORY / "pyramid_verify.cpp"),
                "-o",
                str(cls.executable),
            ],
            check=True,
        )
        subprocess.run(
            [
                "g++",
                "-O3",
                "-std=c++17",
                str(DIRECTORY / "pyramid_6x12_verify.cpp"),
                "-o",
                str(cls.longer_executable),
            ],
            check=True,
        )
        subprocess.run(
            [
                "g++",
                "-O3",
                "-std=c++17",
                str(DIRECTORY / "pyramid_6x10_verify.cpp"),
                "-o",
                str(cls.larger_executable),
            ],
            check=True,
        )
        subprocess.run(
            [
                "g++",
                "-O3",
                "-std=c++17",
                str(DIRECTORY / "pyramid_6x8_verify.cpp"),
                "-o",
                str(cls.strong_executable),
            ],
            check=True,
        )

    @classmethod
    def tearDownClass(cls):
        cls.temporary_directory.cleanup()

    def run_verifier(self, certificate):
        return subprocess.run(
            [str(self.executable), str(certificate)],
            check=False,
            capture_output=True,
            text=True,
        )

    def run_strong_verifier(self, certificate):
        return subprocess.run(
            [str(self.strong_executable), str(certificate)],
            check=False,
            capture_output=True,
            text=True,
        )

    def run_larger_verifier(self, certificate):
        return subprocess.run(
            [str(self.larger_executable), str(certificate)],
            check=False,
            capture_output=True,
            text=True,
        )

    def run_longer_verifier(self, certificate):
        return subprocess.run(
            [str(self.longer_executable), str(certificate)],
            check=False,
            capture_output=True,
            text=True,
        )

    def test_exact_pyramid_certificate(self):
        result = self.run_verifier(DIRECTORY / "pyramid_6x6.cert")
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report["initial_slices"], 1 << 36)
        self.assertEqual(report["maximum_live_weight"], 4704)
        self.assertEqual(report["total_weight"], 8348)
        self.assertEqual(Fraction(report["density_bound"]), Fraction(1176, 2087))
        self.assertLess(
            Fraction(report["density_bound"]), Fraction(12001, 20000)
        )

    def test_tampered_pyramid_certificate_is_rejected(self):
        source = (DIRECTORY / "pyramid_6x6.cert").read_text(encoding="utf-8")
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8") as stream:
            stream.write(source.replace("maximum_live_weight 4704", "maximum_live_weight 4703"))
            stream.flush()
            result = self.run_verifier(stream.name)
        self.assertNotEqual(result.returncode, 0)

    def test_exact_stronger_certificate_and_dual_obstruction(self):
        result = self.run_strong_verifier(DIRECTORY / "pyramid_6x8.cert")
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report["initial_slices"], 1 << 48)
        self.assertEqual(report["maximum_live_weight"], 174312)
        self.assertEqual(report["total_weight"], 312668)
        self.assertEqual(Fraction(report["density_bound"]), Fraction(43578, 78167))
        self.assertLess(
            Fraction(report["density_bound"]), Fraction(1176, 2087)
        )
        self.assertEqual(report["dual_support"], 19)

    def test_tampered_stronger_dual_is_rejected(self):
        source = (DIRECTORY / "pyramid_6x8.cert").read_text(encoding="utf-8")
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8") as stream:
            stream.write(source.replace("witness 281474976710655 12789", "witness 281474976710655 12788"))
            stream.flush()
            result = self.run_strong_verifier(stream.name)
        self.assertNotEqual(result.returncode, 0)

    def test_exact_larger_pyramid_certificate(self):
        result = self.run_larger_verifier(DIRECTORY / "pyramid_6x10.cert")
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report["initial_slices"], 1 << 60)
        self.assertEqual(report["maximum_live_weight"], 555788)
        self.assertEqual(report["total_weight"], 1000004)
        self.assertEqual(Fraction(report["density_bound"]), Fraction(138947, 250001))
        self.assertLess(
            Fraction(report["density_bound"]), Fraction(43578, 78167)
        )

    def test_tampered_larger_pyramid_certificate_is_rejected(self):
        source = (DIRECTORY / "pyramid_6x10.cert").read_text(encoding="utf-8")
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8") as stream:
            stream.write(
                source.replace(
                    "maximum_live_weight 555788",
                    "maximum_live_weight 555787",
                )
            )
            stream.flush()
            result = self.run_larger_verifier(stream.name)
        self.assertNotEqual(result.returncode, 0)

    def test_exact_longer_pyramid_certificate(self):
        result = self.run_longer_verifier(DIRECTORY / "pyramid_6x12.cert")
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report["initial_slices"], 1 << 72)
        self.assertEqual(report["maximum_live_weight"], 555468)
        self.assertEqual(report["total_weight"], 1000004)
        self.assertEqual(
            Fraction(report["density_bound"]), Fraction(138867, 250001)
        )
        self.assertLess(
            Fraction(report["density_bound"]), Fraction(138947, 250001)
        )

    def test_tampered_longer_pyramid_certificate_is_rejected(self):
        source = (DIRECTORY / "pyramid_6x12.cert").read_text(encoding="utf-8")
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8") as stream:
            stream.write(
                source.replace(
                    "maximum_live_weight 555468",
                    "maximum_live_weight 555467",
                )
            )
            stream.flush()
            result = self.run_longer_verifier(stream.name)
        self.assertNotEqual(result.returncode, 0)


if __name__ == "__main__":
    unittest.main()
