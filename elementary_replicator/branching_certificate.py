"""Generate and verify exact finite-phase branching obstruction certificates."""

import argparse
import json
from pathlib import Path

from .theorem import (
    first_phased_capacity_contradiction,
    phased_capacity_at_generation,
)


def generate_certificate(
    substitution: list[list[int]],
    initial_phase: int,
    minimum_phase_population: int,
    width: int,
    height: int,
    period: int,
    radius: int = 1,
) -> dict:
    generation = first_phased_capacity_contradiction(
        substitution,
        initial_phase,
        minimum_phase_population,
        width,
        height,
        period,
        radius,
    )
    counts, required, available = phased_capacity_at_generation(
        substitution,
        initial_phase,
        minimum_phase_population,
        width,
        height,
        period,
        generation,
        radius,
    )
    return {
        "available_cells": available,
        "generation": generation,
        "height": height,
        "initial_phase": initial_phase,
        "minimum_phase_population": minimum_phase_population,
        "period": period,
        "phase_counts": list(counts),
        "radius": radius,
        "required_cells": required,
        "substitution": substitution,
        "width": width,
    }


def verify_certificate(certificate: dict) -> bool:
    expected = generate_certificate(
        certificate["substitution"],
        certificate["initial_phase"],
        certificate["minimum_phase_population"],
        certificate["width"],
        certificate["height"],
        certificate["period"],
        certificate["radius"],
    )
    return certificate == expected


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify", type=Path)
    parser.add_argument("--matrix", default="[[0, 1], [1, 1]]")
    parser.add_argument("--initial-phase", type=int, default=0)
    parser.add_argument("--minimum-population", type=int, default=1)
    parser.add_argument("--width", type=int, default=1)
    parser.add_argument("--height", type=int, default=1)
    parser.add_argument("--period", type=int, default=1)
    parser.add_argument("--radius", type=int, default=1)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    if args.verify:
        certificate = json.loads(args.verify.read_text())
        if not verify_certificate(certificate):
            raise SystemExit("invalid certificate")
        print("valid")
        return

    certificate = generate_certificate(
        json.loads(args.matrix),
        args.initial_phase,
        args.minimum_population,
        args.width,
        args.height,
        args.period,
        args.radius,
    )
    rendered = json.dumps(certificate, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(rendered)
    else:
        print(rendered, end="")


if __name__ == "__main__":
    main()
