#!/usr/bin/env python3
"""Exact, dependency-free verifier for the stored local certificate."""

import argparse
import json
from fractions import Fraction
from pathlib import Path

from model import tile_data


def fractions(values):
    return [Fraction(value) for value in values]


def load_certificate(path: Path):
    with path.open(encoding="utf-8") as stream:
        return json.load(stream)


def verify(certificate: dict) -> dict:
    bound = Fraction(certificate["bound"])
    px = fractions(certificate["potentials"]["x_face"])
    py = fractions(certificate["potentials"]["y_face"])
    pt = fractions(certificate["potentials"]["time_cell"])
    if len(px) != 64 or len(py) != 64 or len(pt) != 2:
        raise AssertionError("wrong potential table dimensions")

    minimum_slack = None
    tight = 0
    for mask in range(512):
        center, nxt, left, right, top, bottom = tile_data(mask)
        rhs = bound + px[left] - px[right] + py[top] - py[bottom] + pt[center] - pt[nxt]
        slack = rhs - center
        if slack < 0:
            raise AssertionError(f"local inequality fails at mask {mask}: slack {slack}")
        minimum_slack = slack if minimum_slack is None else min(minimum_slack, slack)
        tight += slack == 0

    witness = {int(mask): Fraction(weight) for mask, weight in certificate["optimality_witness"].items()}
    if any(weight < 0 for weight in witness.values()):
        raise AssertionError("optimality witness has a negative weight")
    if sum(witness.values()) != 1:
        raise AssertionError("optimality witness is not normalized")

    x_balance = [Fraction(0) for _ in range(64)]
    y_balance = [Fraction(0) for _ in range(64)]
    t_balance = [Fraction(0) for _ in range(2)]
    occupancy = Fraction(0)
    for mask, weight in witness.items():
        center, nxt, left, right, top, bottom = tile_data(mask)
        occupancy += weight * center
        x_balance[left] += weight
        x_balance[right] -= weight
        y_balance[top] += weight
        y_balance[bottom] -= weight
        t_balance[center] += weight
        t_balance[nxt] -= weight
    if any(x_balance) or any(y_balance) or any(t_balance):
        raise AssertionError("optimality witness violates a face-balance equation")
    if occupancy != bound:
        raise AssertionError(f"witness objective {occupancy} does not equal bound {bound}")

    return {"patterns": 512, "bound": str(bound), "tight_patterns": tight, "minimum_slack": str(minimum_slack), "witness_support": len(witness)}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("certificate", nargs="?", type=Path, default=Path(__file__).with_name("certificate.json"))
    args = parser.parse_args()
    print(json.dumps(verify(load_certificate(args.certificate)), sort_keys=True))


if __name__ == "__main__":
    main()
