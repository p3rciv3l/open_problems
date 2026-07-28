#!/usr/bin/env python3
"""Exact SAT search for dense spatially and temporally periodic Life orbits."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from pysat.card import CardEnc, EncType
from pysat.formula import CNF, IDPool
from pysat.solvers import Solver


def life(center: int, neighbors: int) -> int:
    return int(neighbors == 3 or (center and neighbors == 2))


class TorusCNF:
    def __init__(self, width: int, height: int, period: int, symmetry: bool = True):
        if width < 3 or height < 3 or period < 1:
            raise ValueError("width and height must be at least 3; period must be positive")
        self.w, self.h, self.p = width, height, period
        self.pool = IDPool()
        self.cnf = CNF()
        self.cells = [
            self.pool.id(("cell", t, y, x))
            for t in range(period)
            for y in range(height)
            for x in range(width)
        ]
        self._add_life()
        if symmetry:
            self._add_symmetry_breaking()

    def var(self, t: int, y: int, x: int) -> int:
        return self.pool.id(("cell", t % self.p, y % self.h, x % self.w))

    def _add_life(self) -> None:
        offsets = [(dy, dx) for dy in (-1, 0, 1) for dx in (-1, 0, 1) if (dy, dx) != (0, 0)]
        for t in range(self.p):
            for y in range(self.h):
                for x in range(self.w):
                    inputs = [self.var(t, y, x)] + [
                        self.var(t, y + dy, x + dx) for dy, dx in offsets
                    ]
                    output = self.var(t + 1, y, x)
                    for bits in range(512):
                        expected = life(bits & 1, (bits >> 1).bit_count())
                        clause = [
                            -variable if (bits >> i) & 1 else variable
                            for i, variable in enumerate(inputs)
                        ]
                        clause.append(output if expected else -output)
                        self.cnf.append(clause)

    def _lex_geq(self, left: list[int], right: list[int], tag: tuple) -> None:
        prefix = self.pool.id(("lex", tag, 0))
        self.cnf.append([prefix])
        for i, (a, b) in enumerate(zip(left, right)):
            self.cnf.append([-prefix, a, -b])
            nxt = self.pool.id(("lex", tag, i + 1))
            self.cnf.extend(
                [
                    [-nxt, prefix],
                    [-nxt, -a, b],
                    [-nxt, a, -b],
                    [-prefix, -a, -b, nxt],
                    [-prefix, a, b, nxt],
                ]
            )
            prefix = nxt

    def _spatial_maps(self):
        maps = [
            ("id", lambda y, x: (y, x)),
            ("fx", lambda y, x: (y, -x)),
            ("fy", lambda y, x: (-y, x)),
            ("r2", lambda y, x: (-y, -x)),
        ]
        if self.w == self.h:
            maps += [
                ("tr", lambda y, x: (x, y)),
                ("r1", lambda y, x: (x, -y)),
                ("r3", lambda y, x: (-x, y)),
                ("at", lambda y, x: (-x, -y)),
            ]
        return maps

    def _add_symmetry_breaking(self) -> None:
        # Any positive-density orbit can be translated to make this cell live.
        self.cnf.append([self.var(0, 0, 0)])
        base = [
            self.var(t, y, x)
            for t in range(self.p)
            for y in range(self.h)
            for x in range(self.w)
        ]
        for name, transform in self._spatial_maps():
            for dt in range(self.p):
                for dy in range(self.h):
                    for dx in range(self.w):
                        if name == "id" and (dt, dy, dx) == (0, 0, 0):
                            continue
                        shifted = []
                        for t in range(self.p):
                            for y in range(self.h):
                                for x in range(self.w):
                                    yy, xx = transform(y, x)
                                    shifted.append(self.var(t + dt, yy + dy, xx + dx))
                        self._lex_geq(base, shifted, (name, dt, dy, dx))

    def at_least(self, bound: int) -> CNF:
        result = CNF(from_clauses=self.cnf.clauses)
        card = CardEnc.atleast(
            lits=self.cells,
            bound=bound,
            vpool=self.pool,
            encoding=EncType.totalizer,
        )
        result.extend(card.clauses)
        result.nv = max(result.nv, self.pool.top)
        return result


def decode(model: list[int], search: TorusCNF) -> list[list[str]]:
    positive = {literal for literal in model if literal > 0}
    return [
        [
            "".join("o" if search.var(t, y, x) in positive else "." for x in range(search.w))
            for y in range(search.h)
        ]
        for t in range(search.p)
    ]


def rle(rows: list[str]) -> str:
    encoded = []
    for row in rows:
        runs = []
        start = 0
        while start < len(row):
            end = start + 1
            while end < len(row) and row[end] == row[start]:
                end += 1
            count = end - start
            runs.append(("" if count == 1 else str(count)) + ("o" if row[start] == "o" else "b"))
            start = end
        encoded.append("".join(runs).rstrip("b"))
    return "$".join(encoded) + "!"


def orbit_statistics(phases: list[list[str]]) -> tuple[list[int], list[dict[str, int]]]:
    populations = [sum(row.count("o") for row in phase) for phase in phases]
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
    return populations, transitions


def write_artifacts(
    output_dir: Path, width: int, height: int, period: int, cnf_text: str, proof_text: str
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    stem = f"w{width}_h{height}_p{period}"
    (output_dir / f"{stem}.cnf").write_text(cnf_text)
    (output_dir / f"{stem}.drat").write_text(proof_text)


def solve_instance(width: int, height: int, period: int, proof_dir: Path | None = None) -> dict:
    search = TorusCNF(width, height, period)
    volume = width * height * period
    threshold = volume // 2 + 1
    cnf = search.at_least(threshold)
    with Solver(name="g4", bootstrap_with=cnf.clauses, with_proof=True) as solver:
        sat = solver.solve()
        model = solver.get_model() if sat else None
    record = {
        "width": width,
        "height": height,
        "period": period,
        "volume": volume,
        "threshold": threshold,
        "above_half": "SAT" if sat else "UNSAT",
    }
    if sat:
        phases = decode(model, search)
        population = sum(row.count("o") for phase in phases for row in phase)
        populations, transitions = orbit_statistics(phases)
        record.update(
            population=population,
            density=f"{population}/{volume}",
            phases=phases,
            rle=[rle(phase) for phase in phases],
            phase_populations=populations,
            transitions=transitions,
        )
        return record

    maximum_model = None
    maximum_search = None
    maximum = volume // 2
    while maximum > 0:
        candidate_search = TorusCNF(width, height, period)
        candidate_cnf = candidate_search.at_least(maximum)
        with Solver(name="g4", bootstrap_with=candidate_cnf.clauses) as solver:
            if solver.solve():
                maximum_model = solver.get_model()
                maximum_search = candidate_search
                break
        maximum -= 1
    assert maximum_model is not None and maximum_search is not None
    phases = decode(maximum_model, maximum_search)
    population = sum(row.count("o") for phase in phases for row in phase)
    populations, transitions = orbit_statistics(phases)
    assert population == maximum
    record.update(
        maximum_population=maximum,
        maximum_density=f"{maximum}/{volume}",
        maximizer_phases=phases,
        maximizer_rle=[rle(phase) for phase in phases],
        phase_populations=populations,
        transitions=transitions,
        excluded_population=maximum + 1,
    )

    optimality_search = TorusCNF(width, height, period)
    optimality_cnf = optimality_search.at_least(maximum + 1)
    cnf_text = optimality_cnf.to_dimacs()
    record.update(
        cnf_sha256=hashlib.sha256(cnf_text.encode()).hexdigest(),
        variables=optimality_cnf.nv,
        clauses=len(optimality_cnf.clauses),
    )
    with Solver(name="g4", bootstrap_with=optimality_cnf.clauses, with_proof=True) as solver:
        assert not solver.solve()
        proof = solver.get_proof()
    proof_text = "\n".join(proof) + "\n"
    if proof_dir is not None:
        write_artifacts(proof_dir, width, height, period, cnf_text, proof_text)
    record.update(
        cnf_bytes=len(cnf_text.encode()),
        drat_sha256=hashlib.sha256(proof_text.encode()).hexdigest(),
        drat_bytes=len(proof_text.encode()),
    )
    return record


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--width", type=int)
    parser.add_argument("--height", type=int)
    parser.add_argument("--period", type=int)
    parser.add_argument("--range", nargs=3, type=int, metavar=("MIN_SIDE", "MAX_SIDE", "MAX_PERIOD"))
    parser.add_argument("--output", type=Path)
    parser.add_argument("--proof-dir", type=Path)
    args = parser.parse_args()
    if args.range:
        low, high, max_period = args.range
        records = [
            solve_instance(w, h, p, args.proof_dir)
            for w in range(low, high + 1)
            for h in range(low, w + 1)
            for p in range(1, max_period + 1)
        ]
    elif None not in (args.width, args.height, args.period):
        records = [solve_instance(args.width, args.height, args.period, args.proof_dir)]
    else:
        parser.error("give either --range or all of --width, --height, --period")
    text = json.dumps({"format": 1, "instances": records}, indent=2) + "\n"
    if args.output:
        args.output.write_text(text)
    else:
        print(text, end="")


if __name__ == "__main__":
    main()
