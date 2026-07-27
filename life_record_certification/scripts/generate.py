#!/usr/bin/env python3
"""Deterministically generate the witness and all strict-better CNFs."""

import hashlib
import itertools
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts"
N = 4


def var(t, row, col):
    return 1 + t * N * N + row * N + col


def life(alive, neighbors):
    return neighbors == 3 or (alive and neighbors == 2)


def transition_clauses(source_t, target_t):
    clauses = []
    for row in range(N):
        for col in range(N):
            inputs = [(row, col)]
            inputs += [
                ((row + dr) % N, (col + dc) % N)
                for dr in (-1, 0, 1)
                for dc in (-1, 0, 1)
                if (dr, dc) != (0, 0)
            ]
            for bits in itertools.product((False, True), repeat=9):
                expected = life(bits[0], sum(bits[1:]))
                clause = [
                    -var(source_t, r, c) if bit else var(source_t, r, c)
                    for (r, c), bit in zip(inputs, bits)
                ]
                output = var(target_t, row, col)
                clause.append(output if expected else -output)
                clauses.append(clause)
    return clauses


def base_clauses():
    clauses = transition_clauses(0, 1) + transition_clauses(1, 0)
    differences = []
    for row in range(N):
        for col in range(N):
            x, y = var(0, row, col), var(1, row, col)
            d = 33 + row * N + col
            differences.append(d)
            clauses += [[-d, x, y], [-d, -x, -y], [d, -x, y], [d, x, -y]]
    clauses.append(differences)
    return clauses


def bounded_clauses(bound):
    clauses = base_clauses()
    initial = [var(0, row, col) for row in range(N) for col in range(N)]
    clauses += [[-x for x in group] for group in itertools.combinations(initial, bound + 1)]
    return clauses


def write_cnf(path, bound):
    clauses = bounded_clauses(bound)
    with path.open("w", encoding="ascii", newline="\n") as output:
        output.write("c Conway Life B3/S23 on a 4x4 finite torus\n")
        output.write("c exact period 2; population at time 0 <= %d\n" % bound)
        output.write("c vars 1..16=time0, 17..32=time1, 33..48=XOR differences\n")
        output.write(f"p cnf 48 {len(clauses)}\n")
        for clause in clauses:
            output.write(" ".join(map(str, clause)) + " 0\n")


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(65536), b""):
            digest.update(block)
    return digest.hexdigest()


def write_manifest():
    entries = {}
    for path in sorted(ARTIFACTS.rglob("*")):
        if path.is_file() and path.name != "manifest.json":
            entries[str(path.relative_to(ROOT))] = {
                "bytes": path.stat().st_size,
                "sha256": sha256(path),
            }
    manifest = {
        "schema": 1,
        "claim": "The minimum time-0 population of an exact-period-2 state on the 4x4 Life torus is 3.",
        "files": entries,
    }
    (ARTIFACTS / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def main():
    (ARTIFACTS / "cnf").mkdir(parents=True, exist_ok=True)
    witness = {
        "rule": "B3/S23",
        "topology": "4x4_torus",
        "period": 2,
        "population_time_0": 3,
        "states": [
            [[0, 0], [0, 1], [0, 2]],
            [[0, 1], [1, 1], [3, 1]],
        ],
    }
    (ARTIFACTS / "witness.json").write_text(
        json.dumps(witness, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    for bound in range(3):
        write_cnf(ARTIFACTS / "cnf" / f"period2-pop-le-{bound}.cnf", bound)
    write_manifest()


if __name__ == "__main__":
    main()
