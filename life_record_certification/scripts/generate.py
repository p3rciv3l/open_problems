#!/usr/bin/env python3
"""Deterministically generate both Life certification bundles."""

import hashlib
import itertools
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts"
N = 4
GOE_ROWS = [
    "...OO...O..",
    "..O..O.O.O.",
    ".O.O..O...O",
    "O.O.O..O.O.",
    "O..O.O..O..",
    ".O..OOO..O.",
    "..O..O.O..O",
    ".O.O..O.O.O",
    "O...O..O.O.",
    ".O.O.O..O..",
    "..O...OO...",
]


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


def goe_var(row, col):
    return 1 + row * 13 + col


def goe_clauses():
    clauses = []
    for row in range(11):
        for col in range(11):
            positions = [(row + 1, col + 1)]
            positions += [
                (row + 1 + dr, col + 1 + dc)
                for dr in (-1, 0, 1)
                for dc in (-1, 0, 1)
                if dr or dc
            ]
            target = GOE_ROWS[row][col] == "O"
            for bits in itertools.product((False, True), repeat=9):
                if life(bits[0], sum(bits[1:])) == target:
                    continue
                clauses.append(
                    [
                        -goe_var(r, c) if bit else goe_var(r, c)
                        for (r, c), bit in zip(positions, bits)
                    ]
                )
    return clauses


def write_goe_cnf(path):
    clauses = goe_clauses()
    with path.open("w", encoding="ascii", newline="\n") as output:
        output.write("c Predecessor query for Beluchenko's 45-cell 11x11 orphan\n")
        output.write("c B3/S23; target box fully specified; output outside unspecified\n")
        output.write("c vars 1..169 = 13x13 predecessor halo in row-major order\n")
        output.write(f"p cnf 169 {len(clauses)}\n")
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
        "schema": 2,
        "claims": [
            "The minimum time-0 population of an exact-period-2 state on the 4x4 Life torus is 3.",
            "Beluchenko's 45-live-cell 11x11 target box has no B3/S23 predecessor.",
        ],
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
    goe_target = {
        "attribution": "Nicolay Beluchenko, 2009",
        "height": 11,
        "population": 45,
        "rle": "3b2o3bo$2bo2bobobo$bobo2bo3bo$obobo2bobo$o2bobo2bo$bo2b3o2bo$2bo2bobo2bo$bobo2bobobo$o3bo2bobo$bobobo2bo$2bo3b2o!",
        "rows": GOE_ROWS,
        "rule": "B3/S23",
        "width": 11,
    }
    (ARTIFACTS / "goe45-target.json").write_text(
        json.dumps(goe_target, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    write_goe_cnf(ARTIFACTS / "cnf" / "goe45-predecessor.cnf")
    write_manifest()


if __name__ == "__main__":
    main()
