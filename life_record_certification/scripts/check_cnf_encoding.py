#!/usr/bin/env python3
"""Independently reconstruct and compare the intended clauses."""

import itertools
import sys
from collections import Counter
from pathlib import Path

N = 4


def cell(t, row, col):
    return t * 16 + row * 4 + col + 1


def read_dimacs(path):
    clauses, header = [], None
    for line in Path(path).read_text(encoding="ascii").splitlines():
        if not line or line.startswith("c "):
            continue
        if line.startswith("p "):
            _, kind, variables, count = line.split()
            assert kind == "cnf"
            header = int(variables), int(count)
            continue
        values = [int(value) for value in line.split()]
        assert values[-1] == 0 and 0 not in values[:-1]
        clauses.append(tuple(values[:-1]))
    assert header is not None and header[1] == len(clauses)
    return header, clauses


def expected(bound):
    clauses = []
    for source, target in ((0, 1), (1, 0)):
        for row in range(N):
            for col in range(N):
                positions = [(row, col)] + [
                    ((row + dr) % N, (col + dc) % N)
                    for dr in (-1, 0, 1)
                    for dc in (-1, 0, 1)
                    if dr or dc
                ]
                for mask in range(512):
                    bits = [(mask >> index) & 1 for index in range(9)]
                    alive, count = bits[0], sum(bits[1:])
                    born_or_survives = count == 3 or (alive and count == 2)
                    blocked_assignment = tuple(
                        -cell(source, r, c) if bit else cell(source, r, c)
                        for (r, c), bit in zip(positions, bits)
                    )
                    output = cell(target, row, col)
                    clauses.append(blocked_assignment + ((output if born_or_survives else -output),))
    difference_variables = []
    for index in range(16):
        x, y, d = index + 1, index + 17, index + 33
        difference_variables.append(d)
        clauses.extend(
            [(-d, x, y), (-d, -x, -y), (d, -x, y), (d, x, -y)]
        )
    clauses.append(tuple(difference_variables))
    clauses.extend(
        tuple(-variable for variable in group)
        for group in itertools.combinations(range(1, 17), bound + 1)
    )
    return clauses


def expected_goe():
    rows = [
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
    clauses = []
    for row in range(11):
        for col in range(11):
            positions = [(row + 1, col + 1)] + [
                (row + 1 + dr, col + 1 + dc)
                for dr in (-1, 0, 1)
                for dc in (-1, 0, 1)
                if dr or dc
            ]
            wanted = rows[row][col] == "O"
            for mask in range(512):
                bits = [(mask >> index) & 1 for index in range(9)]
                alive, neighbors = bits[0], sum(bits[1:])
                successor = neighbors == 3 or (alive and neighbors == 2)
                if successor == wanted:
                    continue
                clauses.append(
                    tuple(
                        -(r * 13 + c + 1) if bit else r * 13 + c + 1
                        for (r, c), bit in zip(positions, bits)
                    )
                )
    return clauses


def main(paths):
    for name in paths:
        bound = int(Path(name).stem.rsplit("-", 1)[1])
        header, actual = read_dimacs(name)
        wanted = expected(bound)
        assert header[0] == 48
        assert len(actual) == len(set(actual)), f"duplicate clause in {name}"
        assert Counter(actual) == Counter(wanted), name
        print(f"CNF encoding OK: bound {bound}")


def check_goe(path):
    header, actual = read_dimacs(path)
    wanted = expected_goe()
    assert header[0] == 169
    assert len(actual) == len(set(actual)), f"duplicate clause in {path}"
    assert Counter(actual) == Counter(wanted), path
    print("CNF encoding OK: 45-cell GoE predecessor query")


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    if sys.argv[1:]:
        main(sys.argv[1:])
    else:
        main([root / "artifacts/cnf" / f"period2-pop-le-{bound}.cnf" for bound in range(3)])
        check_goe(root / "artifacts/cnf/goe45-predecessor.cnf")
