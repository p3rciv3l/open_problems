#!/usr/bin/env python3
"""Dependency-free exact verifier for the two-center strip certificate."""

import argparse
import json
from fractions import Fraction
from pathlib import Path

from strip2_model import PATTERN_COUNT, tile_data


def load_certificate(path: Path) -> dict:
    with path.open(encoding="utf-8") as stream:
        return json.load(stream)


def verify(certificate: dict) -> dict:
    block_constant = Fraction(certificate["block_constant"])
    density_bound = Fraction(certificate["density_bound"])
    px = [Fraction(value) for value in certificate["potentials"]["x_spacetime_face"]]
    py = [Fraction(value) for value in certificate["potentials"]["y_face"]]
    pt = [Fraction(value) for value in certificate["potentials"]["time_pair"]]
    if len(px) != 1024 or len(py) != 256 or len(pt) != 4:
        raise AssertionError("wrong potential table dimensions")
    if density_bound != block_constant / 2:
        raise AssertionError("density bound is not half the two-center constant")

    minimum_slack = None
    tight = 0
    for mask in range(PATTERN_COUNT):
        center_sum, current, nxt, left, right, top, bottom, _ = tile_data(mask)
        rhs = (
            block_constant
            + px[left]
            - px[right]
            + py[top]
            - py[bottom]
            + pt[current]
            - pt[nxt]
        )
        slack = rhs - center_sum
        if slack < 0:
            raise AssertionError(f"local inequality fails at mask {mask}: {slack}")
        minimum_slack = slack if minimum_slack is None else min(minimum_slack, slack)
        tight += slack == 0

    witness = {
        int(mask): Fraction(weight)
        for mask, weight in certificate["lp_lower_witness"].items()
    }
    if any(weight < 0 for weight in witness.values()) or sum(witness.values()) != 1:
        raise AssertionError("invalid LP lower witness weights")
    x_balance = [Fraction(0) for _ in px]
    y_balance = [Fraction(0) for _ in py]
    t_balance = [Fraction(0) for _ in pt]
    center_average = Fraction(0)
    for mask, weight in witness.items():
        center_sum, current, nxt, left, right, top, bottom, _ = tile_data(mask)
        center_average += weight * center_sum
        x_balance[left] += weight
        x_balance[right] -= weight
        y_balance[top] += weight
        y_balance[bottom] -= weight
        t_balance[current] += weight
        t_balance[nxt] -= weight
    if any(x_balance) or any(y_balance) or any(t_balance):
        raise AssertionError("LP lower witness violates a face-balance equation")
    lp_lower_bound = center_average / 2
    if lp_lower_bound != Fraction(certificate["lp_density_lower_bound"]):
        raise AssertionError("incorrect LP lower bound")

    return {
        "patterns": PATTERN_COUNT,
        "density_bound": str(density_bound),
        "lp_density_lower_bound": str(lp_lower_bound),
        "minimum_slack": str(minimum_slack),
        "tight_patterns": tight,
        "witness_support": len(witness),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "certificate",
        nargs="?",
        type=Path,
        default=Path(__file__).with_name("strip2_certificate.json"),
    )
    args = parser.parse_args()
    print(json.dumps(verify(load_certificate(args.certificate)), sort_keys=True))


if __name__ == "__main__":
    main()
