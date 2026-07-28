from __future__ import annotations

import argparse
import hashlib
import json
import multiprocessing
from pathlib import Path

from pysat.solvers import Solver

from ..still_life.pattern import PeriodicPattern
from ..still_life.period4_transfer import (
    KNOWN_REPRESENTATIVES,
    MARGIN,
    PUMP_OFFSET,
    REPRESENTATIVES,
    Period4Seed,
    classify_periods_at_most_4,
    pump_length_x,
    pump_length_y,
    seed_specs,
    verify_seed,
)
from ..still_life.sat import build_encoding


def _add_equality(clauses, first: int, second: int) -> None:
    clauses.append([-first, second])
    clauses.append([first, -second])


def solve_seed(representative, window, horizontal_pump, vertical_pump):
    pattern = PeriodicPattern(
        REPRESENTATIVES[representative],
        f"bounded-period-representative-{representative}",
    )
    encoding = build_encoding(pattern, window, MARGIN)
    if horizontal_pump:
        start = window.x + PUMP_OFFSET
        length = pump_length_x(representative)
        for y in range(window.y - MARGIN, window.y + window.height + MARGIN):
            for offset in (-2, -1):
                _add_equality(
                    encoding.cnf,
                    encoding.variables[(start + offset, y)],
                    encoding.variables[(start + length + offset, y)],
                )
    if vertical_pump:
        start = window.y + PUMP_OFFSET
        length = pump_length_y(representative)
        for x in range(window.x - MARGIN, window.x + window.width + MARGIN):
            for offset in (-2, -1):
                _add_equality(
                    encoding.cnf,
                    encoding.variables[(x, start + offset)],
                    encoding.variables[(x, start + length + offset)],
                )
    with Solver(name="cadical195", bootstrap_with=encoding.cnf) as solver:
        if not solver.solve():
            raise RuntimeError(
                f"bounded-period seed is UNSAT: {representative}, {window}"
            )
        model = {literal for literal in solver.get_model() if literal > 0}
    seed = Period4Seed(
        representative,
        window,
        frozenset(
            cell for cell, variable in encoding.variables.items() if variable in model
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
        "format": "periods-at-most-4-pump-certificate-v1",
        "theorem": (
            "every rectangular window of every Life still life with horizontal and "
            "vertical periods at most 4 has a finite still-life extension with "
            "margin at most 4"
        ),
        "classification": classify_periods_at_most_4(),
        "search": {
            "solver": "cadical195",
            "cnf_count": len(seeds),
            "clause_count": clause_count,
            "ordered_cnf_sha256": cnf_digest.hexdigest(),
        },
        "summary": {
            "seed_count": len(seeds),
            "new_representative_count": len(REPRESENTATIVES),
            "classified_orbit_count": len(KNOWN_REPRESENTATIVES),
            "margin_bound": MARGIN,
            "pump_offset": PUMP_OFFSET,
        },
        "seed_sha256": hashlib.sha256(payload.encode()).hexdigest(),
        "seeds": seeds,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).with_name("period4_certificate.json"),
    )
    parser.add_argument("--jobs", type=int, default=1)
    args = parser.parse_args()
    certificate = generate(args.jobs)
    args.output.write_text(json.dumps(certificate, indent=2) + "\n")
    print(args.output)


if __name__ == "__main__":
    main()
