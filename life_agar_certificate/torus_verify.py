#!/usr/bin/env python3
"""Solver-independent replay of torus candidates and DRAT certificates."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import tempfile
from pathlib import Path

from pysat.solvers import Solver

from torus_search import TorusCNF, write_artifacts


def step(phase: list[str]) -> list[str]:
    h, w = len(phase), len(phase[0])
    result = []
    for y in range(h):
        row = ""
        for x in range(w):
            neighbors = sum(
                phase[(y + dy) % h][(x + dx) % w] == "o"
                for dy in (-1, 0, 1)
                for dx in (-1, 0, 1)
                if (dy, dx) != (0, 0)
            )
            row += "o" if neighbors == 3 or (phase[y][x] == "o" and neighbors == 2) else "."
        result.append(row)
    return result


def verify_candidate(record: dict) -> None:
    phases = record.get("phases", record.get("maximizer_phases"))
    assert len(phases) == record["period"]
    assert all(len(phase) == record["height"] for phase in phases)
    assert all(len(row) == record["width"] for phase in phases for row in phase)
    assert all(step(phases[t]) == phases[(t + 1) % len(phases)] for t in range(len(phases)))
    population = sum(row.count("o") for phase in phases for row in phase)
    phase_populations = [sum(row.count("o") for row in phase) for phase in phases]
    transitions = []
    for t, current in enumerate(phases):
        following = phases[(t + 1) % len(phases)]
        births = deaths = survivors = 0
        for row, next_row in zip(current, following):
            for cell, next_cell in zip(row, next_row):
                births += cell == "." and next_cell == "o"
                deaths += cell == "o" and next_cell == "."
                survivors += cell == "o" and next_cell == "o"
        transitions.append({"births": births, "deaths": deaths, "survivors": survivors})
    assert record["phase_populations"] == phase_populations
    assert record["transitions"] == transitions
    if record["above_half"] == "SAT":
        assert population == record["population"]
        assert record["density"] == f"{population}/{record['volume']}"
        assert population >= record["threshold"]
    else:
        assert population == record["maximum_population"]
        assert record["maximum_density"] == f"{population}/{record['volume']}"


def regenerate_unsat(record: dict, output: Path, checker: Path) -> None:
    generated = TorusCNF(record["width"], record["height"], record["period"]).at_least(
        record["excluded_population"]
    )
    text = generated.to_dimacs()
    assert hashlib.sha256(text.encode()).hexdigest() == record["cnf_sha256"]
    assert len(text.encode()) == record["cnf_bytes"]
    with Solver(name="g4", bootstrap_with=generated.clauses, with_proof=True) as solver:
        assert not solver.solve()
        proof_text = "\n".join(solver.get_proof()) + "\n"
    assert hashlib.sha256(proof_text.encode()).hexdigest() == record["drat_sha256"]
    assert len(proof_text.encode()) == record["drat_bytes"]
    write_artifacts(
        output, record["width"], record["height"], record["period"], text, proof_text
    )
    stem = f"w{record['width']}_h{record['height']}_p{record['period']}"
    checked = subprocess.run(
        [checker, output / f"{stem}.cnf", output / f"{stem}.drat"],
        capture_output=True,
        text=True,
    )
    assert checked.returncode == 0 and "VERIFIED" in checked.stdout, checked.stdout + checked.stderr


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--drat-trim", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--instance", action="append", help="limit proof regeneration to WxHxP")
    args = parser.parse_args()
    document = json.loads(args.manifest.read_text())
    selected = set(args.instance or [])
    records = document["instances"]
    for record in records:
        verify_candidate(record)
    with tempfile.TemporaryDirectory() as directory:
        output = args.output_dir or Path(directory)
        output.mkdir(parents=True, exist_ok=True)
        proved = 0
        for record in records:
            key = f"{record['width']}x{record['height']}x{record['period']}"
            if record["above_half"] == "UNSAT" and (not selected or key in selected):
                regenerate_unsat(record, output, args.drat_trim)
                proved += 1
    if selected and proved != len(selected):
        raise SystemExit("one or more selected instances were not found")
    print(f"replayed {len(records)} maximizers; regenerated and verified {proved} DRAT proofs")


if __name__ == "__main__":
    main()
