import hashlib
import os
import shutil
import subprocess
import sys
import tempfile
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

    def test_build_creates_missing_proof_directory(self):
        proofs = ROOT / "artifacts" / "proofs"
        with tempfile.TemporaryDirectory() as temporary:
            temporary = Path(temporary)
            saved_proofs = temporary / "proofs"
            fake_solver = temporary / "cadical"
            shutil.copytree(proofs, saved_proofs)
            shutil.rmtree(proofs)
            fake_solver.write_text(
                """#!/usr/bin/env python3
import os
import shutil
import sys
from pathlib import Path

destination = Path(sys.argv[-1])
assert destination.parent.is_dir()
shutil.copy(Path(os.environ["SOURCE_PROOFS"]) / destination.name, destination)
print("s UNSATISFIABLE")
sys.exit(20)
""",
                encoding="utf-8",
            )
            fake_solver.chmod(0o755)
            environment = os.environ.copy()
            environment.update(CADICAL=str(fake_solver), SOURCE_PROOFS=str(saved_proofs))
            try:
                subprocess.run(
                    [ROOT / "scripts" / "build_certificates.sh"],
                    check=True,
                    cwd=ROOT,
                    env=environment,
                )
                self.assertEqual(
                    {path.name for path in proofs.iterdir()},
                    {path.name for path in saved_proofs.iterdir()},
                )
            finally:
                shutil.rmtree(proofs, ignore_errors=True)
                shutil.copytree(saved_proofs, proofs)
                self.run_script("generate.py")

    def test_manifest_and_deterministic_generation(self):
        before = hashlib.sha256((ROOT / "artifacts/manifest.json").read_bytes()).digest()
        self.run_script("generate.py")
        after = hashlib.sha256((ROOT / "artifacts/manifest.json").read_bytes()).digest()
        self.assertEqual(before, after)
        self.run_script("check_manifest.py")


if __name__ == "__main__":
    unittest.main()
