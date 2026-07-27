import hashlib
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class CertificationTests(unittest.TestCase):
    def run_script(self, name, *args):
        subprocess.run(
            [sys.executable, ROOT / "scripts" / name, *args],
            check=True,
            cwd=ROOT,
        )

    def test_witness(self):
        self.run_script("check_witness.py")

    def test_cnf_encoding(self):
        self.run_script("check_cnf_encoding.py")

    def test_drat_proofs(self):
        subprocess.run([ROOT / "scripts" / "verify_proofs.sh"], check=True, cwd=ROOT)

    def test_manifest_and_deterministic_generation(self):
        before = hashlib.sha256((ROOT / "artifacts/manifest.json").read_bytes()).digest()
        self.run_script("generate.py")
        after = hashlib.sha256((ROOT / "artifacts/manifest.json").read_bytes()).digest()
        self.assertEqual(before, after)
        self.run_script("check_manifest.py")


if __name__ == "__main__":
    unittest.main()
