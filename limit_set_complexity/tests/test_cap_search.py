import itertools
import json
import tempfile
import unittest
from pathlib import Path

from pysat.solvers import Solver

from cap_search import (
    Domain,
    band_value,
    cap_cells,
    clause_count,
    dimensions,
    forcing_claim_clauses,
    instance_clauses,
    independently_check_unsat,
    mismatch_literal,
    predecessor_witness_bit,
    replay_witness,
    relation_clauses,
    witness_from_model,
    write_forcing_claim_dimacs,
)
from forcing import OFFSETS, life


def clause_holds(clause, assignment):
    return any((literal > 0) == assignment[abs(literal)] for literal in clause)


class CapEncoderTests(unittest.TestCase):
    def test_relation_cnf_matches_life_truth_table(self):
        inputs = list(range(1, 10))
        output = 10
        clauses = list(relation_clauses(inputs, output))
        center_index = OFFSETS.index((0, 0))
        for bits in itertools.product((0, 1), repeat=9):
            expected = life(
                bits[center_index],
                bits[:center_index] + bits[center_index + 1 :],
            )
            for output_bit in (0, 1):
                assignment = dict(zip(inputs, bits))
                assignment[output] = output_bit
                accepts = all(clause_holds(c, assignment) for c in clauses)
                self.assertEqual(accepts, output_bit == expected)

    def test_marching_band_is_fixed_by_two_life_steps(self):
        first = {}
        for y in range(-1, 5):
            for x in range(-1, 9):
                neighbors = [
                    band_value(x + dx, y + dy)
                    for dx, dy in OFFSETS
                    if (dx, dy) != (0, 0)
                ]
                first[x, y] = life(band_value(x, y), neighbors)
        for y in range(4):
            for x in range(8):
                neighbors = [
                    first[x + dx, y + dy]
                    for dx, dy in OFFSETS
                    if (dx, dy) != (0, 0)
                ]
                self.assertEqual(life(first[x, y], neighbors), band_value(x, y))

    def test_variable_layers_are_disjoint(self):
        domain = Domain(8, 4)
        predecessor = {
            domain.predecessor_var(x, y)
            for y in domain.predecessor_y
            for x in domain.predecessor_x
        }
        middle = {
            domain.middle_var(x, y)
            for y in domain.middle_y
            for x in domain.middle_x
        }
        self.assertFalse(predecessor & middle)
        self.assertEqual(len(predecessor | middle), domain.variables)

    def test_published_cap_geometry(self):
        domain = dimensions(20)
        self.assertEqual((domain.width, domain.height), (48, 44))
        cells = cap_cells(domain)
        self.assertEqual(min(x for x, _ in cells), 10)
        self.assertEqual(max(x for x, _ in cells), 29)
        self.assertEqual(min(y for _, y in cells), -1)
        self.assertEqual(max(y for _, y in cells), 44)
        self.assertEqual(len(cells), 20 * 46)

    def test_candidate_clause_count(self):
        self.assertEqual(clause_count(dimensions(15)), 1_034_392)
        tiny = Domain(1, 1)
        self.assertEqual(
            clause_count(tiny), sum(1 for _ in instance_clauses(tiny))
        )

    def test_sat_witness_replays_under_life(self):
        domain = Domain(1, 1)
        with Solver(
            name="cadical195", bootstrap_with=instance_clauses(domain)
        ) as solver:
            self.assertTrue(solver.solve())
            witness = witness_from_model(domain, solver.get_model())
        self.assertTrue(replay_witness(domain, witness))
        witness["middle"][0] = (
            ("1" if witness["middle"][0][0] == "0" else "0")
            + witness["middle"][0][1:]
        )
        self.assertFalse(replay_witness(domain, witness))

    def test_combined_claim_asserts_some_mismatch(self):
        padding = 1
        domain = dimensions(padding)
        cells = [(0, 0), (1, 0)]
        clauses = list(forcing_claim_clauses(padding, 0, 0, cells))
        self.assertEqual(
            clauses[-1],
            [mismatch_literal(domain, 0, 0, cell) for cell in cells],
        )
        self.assertEqual(
            len(clauses), clause_count(domain) + 1
        )

    def test_dimacs_is_reparsed_for_independent_check(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "claim.cnf"
            report = write_forcing_claim_dimacs(
                path, 1, 0, 0, [(0, 0), (1, 0)]
            )
            self.assertEqual(report["clauses"], clause_count(dimensions(1)) + 1)
            with path.open("a") as output:
                variable = dimensions(1).predecessor_var(0, 0)
                output.write(f"{variable} 0\n{-variable} 0\n")
            lines = path.read_text().splitlines()
            parts = lines[0].split()
            parts[-1] = str(int(parts[-1]) + 2)
            lines[0] = " ".join(parts)
            path.write_text("\n".join(lines) + "\n")
            self.assertTrue(independently_check_unsat(path, "glucose42"))

    def test_checked_slice_countermodels_replay(self):
        result_path = Path(__file__).parents[1] / "slice_result.json"
        report = json.loads(result_path.read_text())
        domain = dimensions(report["padding"])
        self.assertTrue(report["certificate"]["checked_unsat"])
        nonforced = [result for result in report["results"] if not result["forced"]]
        self.assertEqual(len(nonforced), 13)
        for result in nonforced:
            x, y = result["cell"]
            self.assertTrue(
                replay_witness(domain, result["witness"], *report["phase"])
            )
            self.assertEqual(
                predecessor_witness_bit(domain, result["witness"], x, y),
                result["witnessed"],
            )
            self.assertNotEqual(result["expected"], result["witnessed"])


if __name__ == "__main__":
    unittest.main()
