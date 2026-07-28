#!/usr/bin/env python3
"""Exclude noncontracting transitions among all marching-band phases."""

from __future__ import annotations

import argparse
import itertools
import json
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from pysat.solvers import Solver

from cap_search import (
    Domain,
    band_value,
    dimensions,
    instance_clauses,
    mismatch_literal,
    predecessor_witness_bit,
    replay_witness,
    witness_from_model,
)


PHASES = tuple(itertools.product(range(8), range(4)))


def placements(domain: Domain) -> tuple[tuple[int, int], ...]:
    return tuple(itertools.product(range(-2, 3), repeat=2))


def phase_rectangle_differs(
    phase: tuple[int, int],
    other: tuple[int, int],
    origin: tuple[int, int],
    width: int,
    height: int,
) -> bool:
    ox, oy = origin
    return any(
        band_value(x, y, *phase) != band_value(x, y, *other)
        for y in range(oy, oy + height)
        for x in range(ox, ox + width)
    )


def reflected_phase(phase: tuple[int, int], width: int, height: int) -> tuple[int, int]:
    values = tuple(
        band_value(x, height - 1 - y, *phase)
        for y in range(height)
        for x in range(width)
    )
    for other in PHASES:
        if values == tuple(
            band_value(x, y, *other)
            for y in range(height)
            for x in range(width)
        ):
            return other
    raise RuntimeError(f"{phase}: reflected pattern is not a marching-band phase")


def reflect_witness(witness: dict) -> dict:
    return {
        layer: list(reversed(witness[layer]))
        for layer in ("predecessor", "middle")
    }


def phase_result(
    phase: tuple[int, int],
    flipped_cell: tuple[int, int],
    witness: dict,
    queries: int | str,
    domain: Domain,
) -> dict:
    if not replay_witness(domain, witness, *phase):
        raise RuntimeError(f"{phase}: SAT witness does not replay")
    if (
        predecessor_witness_bit(domain, witness, *flipped_cell)
        == band_value(*flipped_cell, *phase)
    ):
        raise RuntimeError(f"{phase}: SAT witness does not flip the selected cell")

    distinct_phase_checks = [
        {
            "destination_phase": list(other),
            "all_placements_differ_from_canonical_predecessor": all(
                phase_rectangle_differs(
                    phase, other, origin, domain.width, domain.height
                )
                for origin in placements(domain)
            ),
        }
        for other in PHASES
        if other != phase
    ]
    if not all(
        check["all_placements_differ_from_canonical_predecessor"]
        for check in distinct_phase_checks
    ):
        raise RuntimeError(f"{phase}: two nominal phases coincide on a placement")

    return {
        "source_phase": list(phase),
        "same_phase_counterexample": {
            "cell": list(flipped_cell),
            "queries_before_witness": queries,
            "expected": band_value(*flipped_cell, *phase),
            "witnessed": predecessor_witness_bit(domain, witness, *flipped_cell),
            "replayed": True,
            "witness": witness,
        },
        "other_phase_counterexample": (
            "the canonical source-phase predecessor replays and differs from every "
            "other phase on every placement"
        ),
        "distinct_phase_checks": distinct_phase_checks,
        "outgoing_edges": [],
    }


def analyze_phase(
    phase: tuple[int, int],
    solver_name: str = "cadical195",
    padding: int = 15,
) -> dict:
    domain = dimensions(padding)
    common_cells = [
        (x, y)
        for y in range(2, domain.height - 2)
        for x in range(2, domain.width - 2)
    ]
    common_cells.sort(
        key=lambda cell: (
            abs(cell[1] - domain.height // 2),
            abs(cell[0] - 29),
        )
    )

    with Solver(
        name=solver_name,
        bootstrap_with=instance_clauses(domain, *phase),
    ) as solver:
        flipped_cell = None
        witness = None
        queries = 0
        for cell in common_cells:
            queries += 1
            if solver.solve(
                assumptions=[mismatch_literal(domain, *phase, cell)]
            ):
                flipped_cell = cell
                witness = witness_from_model(domain, solver.get_model())
                break
    if flipped_cell is None or witness is None:
        raise RuntimeError(f"{phase}: complete common core is forced")

    return phase_result(phase, flipped_cell, witness, queries, domain)


def search_type_family(
    workers: int,
    solver_name: str = "cadical195",
    padding: int = 15,
) -> dict:
    domain = dimensions(padding)
    representatives = tuple(
        phase
        for phase in PHASES
        if phase < reflected_phase(phase, domain.width, domain.height)
    )
    with ProcessPoolExecutor(max_workers=workers) as executor:
        representative_results = list(
            executor.map(
                analyze_phase,
                representatives,
                itertools.repeat(solver_name),
                itertools.repeat(padding),
            )
        )
    by_phase = {
        tuple(result["source_phase"]): result for result in representative_results
    }
    for phase, result in tuple(by_phase.items()):
        other = reflected_phase(phase, domain.width, domain.height)
        cell = tuple(result["same_phase_counterexample"]["cell"])
        reflected_cell = (cell[0], domain.height - 1 - cell[1])
        by_phase[other] = phase_result(
            other,
            reflected_cell,
            reflect_witness(result["same_phase_counterexample"]["witness"]),
            f"derived by vertical reflection from phase {phase}",
            domain,
        )
    results = [by_phase[phase] for phase in PHASES]
    return {
        "theorem": (
            "For every marching-band phase target on the 38x34 box, and hence "
            "for every subtarget obtained by deleting constraints in that box, "
            "no complete 38x34 marching-band phase type is forced at any of the "
            "25 placements in the two-step predecessor domain."
        ),
        "scope": {
            "time_steps": 2,
            "source_types": len(PHASES),
            "destination_types": len(PHASES),
            "output_size": [domain.width, domain.height],
            "predecessor_size": [
                len(domain.predecessor_x),
                len(domain.predecessor_y),
            ],
            "destination_placements": [
                list(origin) for origin in placements(domain)
            ],
            "target_shapes": (
                "all subsets of the output box whose fixed values agree with "
                "the selected source phase"
            ),
            "sat_searched_phases": [list(phase) for phase in representatives],
            "reflection_derived_phases": [
                list(reflected_phase(phase, domain.width, domain.height))
                for phase in representatives
            ],
        },
        "proof": {
            "same_phase": (
                "the recorded SAT predecessor flips a cell common to all 25 "
                "noncontracting placements; both Life steps are replayed directly"
            ),
            "different_phase": (
                "the canonical source phase is a two-step predecessor and a "
                "direct exhaustive comparison finds a disagreement with each "
                "destination phase in every placement"
            ),
            "shape_monotonicity": (
                "each full-box predecessor is also a predecessor after any "
                "output constraints are deleted"
            ),
        },
        "transition_graph": {
            "vertices": [list(phase) for phase in PHASES],
            "edges": [],
            "contains_cycle": False,
        },
        "solver": solver_name,
        "results": results,
        "passed": len(results) == len(PHASES)
        and all(not result["outgoing_edges"] for result in results),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--solver", default="cadical195")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = search_type_family(args.workers, args.solver)
    rendered = json.dumps(report, indent=2)
    if args.output:
        args.output.write_text(rendered + "\n")
    print(rendered)
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
