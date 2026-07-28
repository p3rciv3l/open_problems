#!/usr/bin/env python3
"""Dependency-free exact verifier for the 4 x 4 cluster certificate."""

import argparse
import json
from fractions import Fraction
from pathlib import Path


WIDTH = HEIGHT = 4
PATTERN_COUNT = 1 << (WIDTH * HEIGHT)


def bit(mask: int, x: int, y: int) -> int:
    return (mask >> (x + WIDTH * y)) & 1


def encode(values) -> int:
    return sum(value << index for index, value in enumerate(values))


def output(mask: int, x: int, y: int) -> int:
    center = bit(mask, x, y)
    neighbors = 0
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            if dx or dy:
                neighbors += bit(mask, x + dx, y + dy)
    return int(neighbors == 3 or (center and neighbors == 2))


def input_face_codes(mask: int) -> tuple[int, int, int, int]:
    left = encode(bit(mask, x, y) for y in range(HEIGHT) for x in range(3))
    right = encode(bit(mask, x, y) for y in range(HEIGHT) for x in range(1, 4))
    top = encode(bit(mask, x, y) for y in range(3) for x in range(WIDTH))
    bottom = encode(bit(mask, x, y) for y in range(1, 4) for x in range(WIDTH))
    return left, right, top, bottom


def spacetime_face_codes(mask: int) -> tuple[int, int, int, int]:
    left, right, top, bottom = input_face_codes(mask)
    left |= encode(output(mask, 1, y) for y in (1, 2)) << 12
    right |= encode(output(mask, 2, y) for y in (1, 2)) << 12
    top |= encode(output(mask, x, 1) for x in (1, 2)) << 12
    bottom |= encode(output(mask, x, 2) for x in (1, 2)) << 12
    return left, right, top, bottom


def temporal_codes(mask: int) -> tuple[int, int]:
    current = encode(bit(mask, x, y) for y in (1, 2) for x in (1, 2))
    following = encode(output(mask, x, y) for y in (1, 2) for x in (1, 2))
    return current, following


def add_balance(balance, source, target, weight):
    balance[source] = balance.get(source, Fraction(0)) + weight
    balance[target] = balance.get(target, Fraction(0)) - weight


def transform(mask: int, symmetry: int) -> int:
    result = 0
    for y in range(HEIGHT):
        for x in range(WIDTH):
            target_x, target_y = x, y
            if symmetry >= 4:
                target_x = WIDTH - 1 - target_x
            for _ in range(symmetry % 4):
                target_x, target_y = WIDTH - 1 - target_y, target_x
            result |= bit(mask, x, y) << (target_x + WIDTH * target_y)
    return result


def verify(certificate: dict) -> dict:
    if certificate.get("width") != WIDTH or certificate.get("height") != HEIGHT:
        raise AssertionError("wrong cluster dimensions")
    bound = Fraction(certificate["bound"])
    px = [Fraction(value) for value in certificate["dual"]["x_input_face"]]
    py = [Fraction(value) for value in certificate["dual"]["y_input_face"]]
    pt = [Fraction(value) for value in certificate["dual"]["time_interior"]]
    if len(px) != 4096 or len(py) != 4096 or len(pt) != 16:
        raise AssertionError("wrong dual table dimensions")
    if certificate["dual"].get("symmetrized") is not True:
        raise AssertionError("dual must declare its orbit symmetrization")

    minimum_slack = None
    tight = 0
    seen = set()
    for mask in range(PATTERN_COUNT):
        if mask in seen:
            continue
        orbit = {transform(mask, symmetry) for symmetry in range(8)}
        seen.update(orbit)
        slack = len(orbit) * bound
        for image in orbit:
            left, right, top, bottom = input_face_codes(image)
            current, following = temporal_codes(image)
            slack += (
                px[left]
                - px[right]
                + py[top]
                - py[bottom]
                + pt[current]
                - pt[following]
                - bit(image, 1, 1)
            )
        if slack < 0:
            raise AssertionError(f"dual orbit inequality fails at mask {mask}: {slack}")
        minimum_slack = slack if minimum_slack is None else min(minimum_slack, slack)
        tight += slack == 0

    witness = {
        int(mask): Fraction(weight)
        for mask, weight in certificate["primal"].items()
    }
    if any(weight <= 0 for weight in witness.values()) or sum(witness.values()) != 1:
        raise AssertionError("invalid primal weights")
    x_balance = {}
    y_balance = {}
    time_balance = {}
    objective = Fraction(0)
    for mask, weight in witness.items():
        if not 0 <= mask < PATTERN_COUNT:
            raise AssertionError("primal mask out of range")
        left, right, top, bottom = spacetime_face_codes(mask)
        current, following = temporal_codes(mask)
        add_balance(x_balance, left, right, weight)
        add_balance(y_balance, top, bottom, weight)
        add_balance(time_balance, current, following, weight)
        objective += weight * bit(mask, 1, 1)
    if any(x_balance.values()) or any(y_balance.values()) or any(time_balance.values()):
        raise AssertionError("primal violates a spacetime marginal balance")
    if objective != bound:
        raise AssertionError(f"primal value {objective} does not match bound {bound}")

    return {
        "bound": str(bound),
        "patterns": PATTERN_COUNT,
        "primal_support": len(witness),
        "tight_orbits": tight,
        "minimum_slack": str(minimum_slack),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "certificate",
        nargs="?",
        type=Path,
        default=Path(__file__).with_name("cluster_4x4_certificate.json"),
    )
    args = parser.parse_args()
    with args.certificate.open(encoding="utf-8") as stream:
        certificate = json.load(stream)
    print(json.dumps(verify(certificate), sort_keys=True))


if __name__ == "__main__":
    main()
