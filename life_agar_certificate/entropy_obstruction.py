#!/usr/bin/env python3
"""Exact checks for the entropy and local-marginal obstructions."""

import itertools
import json
from fractions import Fraction
from pathlib import Path

from model import tile_data


def step(cells: frozenset[tuple[int, int]], width: int, height: int):
    result = set()
    for y in range(height):
        for x in range(width):
            neighbors = sum(
                ((x + dx) % width, (y + dy) % height) in cells
                for dy in (-1, 0, 1)
                for dx in (-1, 0, 1)
                if dx or dy
            )
            alive = (x, y) in cells
            if neighbors == 3 or (alive and neighbors == 2):
                result.add((x, y))
    return frozenset(result)


def blinker_configuration(labels, side: int, spacing: int):
    cells = set()
    for index, label in enumerate(labels):
        if label == 0:
            continue
        center_x = (index % side) * spacing
        center_y = (index // side) * spacing
        if label == 1:
            offsets = ((-1, 0), (0, 0), (1, 0))
        else:
            offsets = ((0, -1), (0, 0), (0, 1))
        cells.update(
            (
                (center_x + dx) % (side * spacing),
                (center_y + dy) % (side * spacing),
            )
            for dx, dy in offsets
        )
    return frozenset(cells)


def verify_blinker_product(spacing=5, side=2):
    checked = 0
    for labels in itertools.product(range(3), repeat=side * side):
        expected = tuple(0 if label == 0 else 3 - label for label in labels)
        cells = blinker_configuration(labels, side, spacing)
        evolved = step(cells, side * spacing, side * spacing)
        if evolved != blinker_configuration(expected, side, spacing):
            raise AssertionError(f"interacting blinkers for labels {labels}")
        checked += 1
    return checked


def verify_local_witness(path: Path):
    with path.open(encoding="utf-8") as stream:
        certificate = json.load(stream)
    witness = {
        int(mask): Fraction(weight)
        for mask, weight in certificate["optimality_witness"].items()
    }
    if sum(witness.values()) != 1 or any(weight <= 0 for weight in witness.values()):
        raise AssertionError("invalid witness probabilities")

    balances = [[Fraction(0) for _ in range(size)] for size in (64, 64, 2)]
    occupancy = Fraction(0)
    output_occupancy = Fraction(0)
    for mask, weight in witness.items():
        center, nxt, left, right, top, bottom = tile_data(mask)
        occupancy += weight * center
        output_occupancy += weight * nxt
        balances[0][left] += weight
        balances[0][right] -= weight
        balances[1][top] += weight
        balances[1][bottom] -= weight
        balances[2][center] += weight
        balances[2][nxt] -= weight
    if any(value for balance in balances for value in balance):
        raise AssertionError("witness is not locally stationary")
    if occupancy != Fraction(8, 13) or output_occupancy != occupancy:
        raise AssertionError("wrong witness density")
    return len(witness), occupancy


def analyze(directory: Path):
    support, occupancy = verify_local_witness(directory / "certificate.json")
    return {
        "local_witness_density": str(occupancy),
        "local_witness_support": support,
        "blinker_spacing": 5,
        "blinker_labelings_checked": verify_blinker_product(),
        "blinker_density": "3*q/25",
        "blinker_activity": "4*q/25",
        "blinker_entropy_bits_per_cell": "(H_2(q)+q)/25",
    }


if __name__ == "__main__":
    print(json.dumps(analyze(Path(__file__).resolve().parent), sort_keys=True))
