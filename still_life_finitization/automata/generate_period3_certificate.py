from __future__ import annotations

import argparse
import hashlib
import json
import multiprocessing
from pathlib import Path

from pysat.solvers import Solver

from ..still_life.period3_transfer import (
    MARGIN,
    PUMP_LENGTH,
    PUMP_OFFSET,
    PUMP_THRESHOLD,
    REPRESENTATIVES,
    Period3Seed,
    classify_period3_tiles,
    seed_specs,
    verify_seed,
)
from ..still_life.pattern import PeriodicPattern
from ..still_life.sat import build_encoding


def _add_equality(clauses, first: int, second: int) -> None:
    clauses.append([-first, second])
    clauses.append([first, -second])


def solve_seed(representative, window, horizontal_pump, vertical_pump):
    pattern = PeriodicPattern(
        REPRESENTATIVES[representative], f"period-3-representative-{representative}"
    )
    encoding = build_encoding(pattern, window, MARGIN)
    if horizontal_pump:
        start = window.x + PUMP_OFFSET
        for y in range(window.y - MARGIN, window.y + window.height + MARGIN):
            _add_equality(
                encoding.cnf,
                encoding.variables[(start - 2, y)],
                encoding.variables[(start + PUMP_LENGTH - 2, y)],
            )
            _add_equality(
                encoding.cnf,
                encoding.variables[(start - 1, y)],
                encoding.variables[(start + PUMP_LENGTH - 1, y)],
            )
    if vertical_pump:
        start = window.y + PUMP_OFFSET
        for x in range(window.x - MARGIN, window.x + window.width + MARGIN):
            _add_equality(
                encoding.cnf,
                encoding.variables[(x, start - 2)],
                encoding.variables[(x, start + PUMP_LENGTH - 2)],
            )
            _add_equality(
                encoding.cnf,
                encoding.variables[(x, start - 1)],
                encoding.variables[(x, start + PUMP_LENGTH - 1)],
            )
    with Solver(name="cadical195", bootstrap_with=encoding.cnf) as solver:
        if not solver.solve():
            raise RuntimeError(
                f"period-3 seed is UNSAT: {representative}, {window}"
            )
        model = {literal for literal in solver.get_model() if literal > 0}
    seed = Period3Seed(
        representative,
        window,
        frozenset(
            cell
            for cell, variable in encoding.variables.items()
            if variable in model
        ),
        horizontal_pump,
        vertical_pump,
    )
    errors = verify_seed(seed)
    if errors:
        raise RuntimeError("; ".join(errors))
    return seed, encoding


def _solve_record(spec):
    seed, encoding = solve_seed(*spec)
    return seed.to_dict(), encoding.digest(), len(encoding.cnf.clauses)


def generate(jobs: int = 1) -> dict[str, object]:
    seeds = []
    cnf_digest = hashlib.sha256()
    clause_count = 0
    specs = list(seed_specs())
    if jobs == 1:
        records = map(_solve_record, specs)
        pool = None
    else:
        pool = multiprocessing.Pool(jobs)
        records = pool.imap(_solve_record, specs, chunksize=8)
    try:
        for seed, digest, clauses in records:
            seeds.append(seed)
            cnf_digest.update((digest + "\n").encode())
            clause_count += clauses
    finally:
        if pool is not None:
            pool.close()
            pool.join()
    payload = json.dumps(seeds, sort_keys=True, separators=(",", ":"))
    return {
        "format": "period-3-pump-certificate-v1",
        "theorem": (
            "every rectangular window of every 3-by-3-periodic Life still life "
            "has a finite still-life extension with margin at most 4"
        ),
        "classification": classify_period3_tiles(),
        "search": {
            "solver": "cadical195",
            "cnf_count": len(seeds),
            "clause_count": clause_count,
            "ordered_cnf_sha256": cnf_digest.hexdigest(),
        },
        "summary": {
            "seed_count": len(seeds),
            "representative_count": len(REPRESENTATIVES),
            "phase_count": 9,
            "margin_bound": MARGIN,
            "pump_threshold": PUMP_THRESHOLD,
            "pump_length": PUMP_LENGTH,
        },
        "seed_sha256": hashlib.sha256(payload.encode()).hexdigest(),
        "seeds": seeds,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).with_name("period3_certificate.json"),
    )
    parser.add_argument("--jobs", type=int, default=1)
    args = parser.parse_args()
    certificate = generate(args.jobs)
    args.output.write_text(json.dumps(certificate, indent=2) + "\n")
    print(args.output)


if __name__ == "__main__":
    main()
