#!/usr/bin/env python3
"""Exact diagnostics for the nonrepeatable three-layer pyramid obstruction."""

import argparse
import json
from collections import defaultdict
from fractions import Fraction
from pathlib import Path


def read_certificate(path):
    lines = path.read_text(encoding="utf-8").splitlines()
    total = maximum = dual_total = None
    layers = []
    witnesses = []
    index = 0
    while index < len(lines):
        fields = lines[index].split()
        if not fields or fields[0].startswith("#"):
            index += 1
            continue
        if fields[0] == "total_weight":
            total = int(fields[1])
        elif fields[0] == "maximum_live_weight":
            maximum = int(fields[1])
        elif fields[0] == "dual_total":
            dual_total = int(fields[1])
        elif fields[0] == "layer":
            width, height = map(int, fields[1:])
            layers.append(
                [
                    list(map(int, lines[index + row + 1].split()))
                    for row in range(height)
                ]
            )
            if any(len(row) != width for row in layers[-1]):
                raise ValueError("wrong layer width")
            index += height
        elif fields[0] == "witness":
            witnesses.append((int(fields[1]), int(fields[2])))
        index += 1
    if total is None or maximum is None or len(layers) != 3:
        raise ValueError("incomplete pyramid certificate")
    if witnesses and (
        dual_total is None or sum(mass for _, mass in witnesses) != dual_total
    ):
        raise ValueError("invalid dual normalization")
    return {
        "total": total,
        "maximum": maximum,
        "layers": layers,
        "dual_total": dual_total,
        "witnesses": witnesses,
    }


def life(grid):
    output = []
    for y in range(1, len(grid) - 1):
        row = []
        for x in range(1, len(grid[0]) - 1):
            center = grid[y][x]
            neighbors = (
                sum(
                    grid[y + dy][x + dx]
                    for dy in (-1, 0, 1)
                    for dx in (-1, 0, 1)
                )
                - center
            )
            row.append(int(neighbors == 3 or (center and neighbors == 2)))
        output.append(row)
    return output


def initial_grid(mask, height):
    return [[(mask >> (x + 6 * y)) & 1 for x in range(6)] for y in range(height)]


def weighted_score(grids, weights):
    return sum(
        cell * weight
        for grid, layer in zip(grids, weights)
        for row, weight_row in zip(grid, layer)
        for cell, weight in zip(row, weight_row)
    )


def transition_counts(current, following):
    survivors = deaths = births = 0
    for y in range(1, len(current) - 1):
        for x in range(1, len(current[0]) - 1):
            before = current[y][x]
            after = following[y - 1][x - 1]
            survivors += before * after
            deaths += before * (1 - after)
            births += (1 - before) * after
    return survivors, deaths, births


def reflected_grids(grid):
    return (
        grid,
        [row[::-1] for row in grid],
        grid[::-1],
        [row[::-1] for row in grid[::-1]],
    )


def block_mask(grid, x0, y0, width, height):
    return sum(
        grid[y0 + y][x0 + x] << (x + width * y)
        for y in range(height)
        for x in range(width)
    )


def overlap_defect(distribution, axis):
    left = defaultdict(Fraction)
    right = defaultdict(Fraction)
    height, width = len(distribution[0][0]), len(distribution[0][0][0])
    for grid, mass in distribution:
        if axis == "x":
            first = block_mask(grid, 0, 0, width - 1, height)
            second = block_mask(grid, 1, 0, width - 1, height)
        else:
            first = block_mask(grid, 0, 0, width, height - 1)
            second = block_mask(grid, 0, 1, width, height - 1)
        left[first] += mass
        right[second] += mass
    support = left.keys() | right.keys()
    total_variation = sum(abs(left[key] - right[key]) for key in support) / 2
    event = max(support, key=lambda key: abs(left[key] - right[key]))
    return total_variation, event, left[event] - right[event]


def fraction(value):
    if value.denominator == 1:
        return str(value)
    return f"{value.numerator}/{value.denominator}"


def maximizing_extinction_report(certificate, height):
    full = (1 << (6 * height)) - 1
    if height in (8, 12):
        for bit in (0, 5, 6 * (height - 1), 6 * height - 1):
            full ^= 1 << bit
    grids = [initial_grid(full, height)]
    grids.extend((life(grids[0]), life(life(grids[0]))))
    score = weighted_score(grids, certificate["layers"])
    if score != certificate["maximum"]:
        raise AssertionError("stored extinction slice is not maximizing")
    return {
        "initial_mask": str(full),
        "live_counts": [sum(map(sum, grid)) for grid in grids],
        "score": score,
    }


def dual_report(certificate):
    total = certificate["dual_total"]
    if total is None:
        raise ValueError("certificate has no dual distribution")
    expected_live = [Fraction() for _ in range(3)]
    expected_transitions = [[Fraction() for _ in range(3)] for _ in range(2)]
    layer_distributions = [[] for _ in range(3)]
    for mask, integer_mass in certificate["witnesses"]:
        mass = Fraction(integer_mass, total)
        grids = [initial_grid(mask, 8)]
        grids.extend((life(grids[0]), life(life(grids[0]))))
        for layer, grid in enumerate(grids):
            expected_live[layer] += mass * sum(map(sum, grid))
            layer_distributions[layer].extend(
                (reflected, mass / 4) for reflected in reflected_grids(grid)
            )
        for generation in range(2):
            counts = transition_counts(grids[generation], grids[generation + 1])
            for kind, count in enumerate(counts):
                expected_transitions[generation][kind] += mass * count
    defects = []
    for layer, distribution in enumerate(layer_distributions):
        for axis in ("x", "y"):
            variation, event, imbalance = overlap_defect(distribution, axis)
            defects.append(
                {
                    "layer": layer,
                    "axis": axis,
                    "total_variation": fraction(variation),
                    "event": str(event),
                    "event_imbalance": fraction(imbalance),
                }
            )
    for survivors, deaths, births in expected_transitions:
        if deaths != births:
            raise AssertionError("dual does not have balanced temporal live flux")
    return {
        "support": len(certificate["witnesses"]),
        "expected_live": [fraction(value) for value in expected_live],
        "expected_transitions": [
            [fraction(value) for value in transition]
            for transition in expected_transitions
        ],
        "overlap_defects": defects,
    }


def analyze(directory):
    reports = {}
    for height in (8, 10, 12):
        certificate = read_certificate(directory / f"pyramid_6x{height}.cert")
        reports[f"6x{height}"] = maximizing_extinction_report(certificate, height)
        if height == 8:
            reports["6x8"]["dual"] = dual_report(certificate)
    return reports


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--directory", type=Path, default=Path(__file__).resolve().parent
    )
    args = parser.parse_args()
    print(json.dumps(analyze(args.directory), sort_keys=True))


if __name__ == "__main__":
    main()
