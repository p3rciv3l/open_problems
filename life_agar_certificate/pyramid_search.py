#!/usr/bin/env python3
"""Sparse LP/CP-SAT column generation for the 6x6 Life pyramid."""

import argparse
import json
import math
import random
from fractions import Fraction
from pathlib import Path

import numpy as np
from ortools.sat.python import cp_model
from scipy.optimize import linprog


SIZES = (6, 4, 2)


def orbit_key(size, x, y):
    images = (
        (x, y),
        (size - 1 - x, y),
        (x, size - 1 - y),
        (size - 1 - x, size - 1 - y),
        (y, x),
        (size - 1 - y, x),
        (y, size - 1 - x),
        (size - 1 - y, size - 1 - x),
    )
    return min(images)


def make_orbits():
    orbits = []
    position_orbit = []
    multiplicities = []
    for layer, size in enumerate(SIZES):
        layer_orbits = {}
        positions = {}
        for y in range(size):
            for x in range(size):
                key = orbit_key(size, x, y)
                if key not in layer_orbits:
                    layer_orbits[key] = len(orbits)
                    orbits.append((layer, key))
                    multiplicities.append(0)
                index = layer_orbits[key]
                positions[x, y] = index
                multiplicities[index] += 1
        position_orbit.append(positions)
    return orbits, position_orbit, multiplicities


ORBITS, POSITION_ORBIT, MULTIPLICITIES = make_orbits()


def life_grid(grid):
    size = len(grid)
    output = []
    for y in range(1, size - 1):
        row = []
        for x in range(1, size - 1):
            center = grid[y][x]
            neighbors = sum(
                grid[y + dy][x + dx]
                for dy in (-1, 0, 1)
                for dx in (-1, 0, 1)
            ) - center
            row.append(int(neighbors == 3 or (center and neighbors == 2)))
        output.append(row)
    return output


def count_vector(mask):
    grid = [
        [(mask >> (x + 6 * y)) & 1 for x in range(6)] for y in range(6)
    ]
    layers = [grid, life_grid(grid)]
    layers.append(life_grid(layers[-1]))
    counts = [0] * len(ORBITS)
    for layer, size in enumerate(SIZES):
        for y in range(size):
            for x in range(size):
                counts[POSITION_ORBIT[layer][x, y]] += layers[layer][y][x]
    return tuple(counts)


class Separator:
    def __init__(self):
        self.model = cp_model.CpModel()
        self.layers = [
            [
                [self.model.NewBoolVar(f"x{layer}_{x}_{y}") for x in range(size)]
                for y in range(size)
            ]
            for layer, size in enumerate(SIZES)
        ]
        allowed = [
            (center, neighbors, int(neighbors == 3 or (center and neighbors == 2)))
            for center in (0, 1)
            for neighbors in range(9)
        ]
        for layer in range(len(SIZES) - 1):
            source = self.layers[layer]
            target = self.layers[layer + 1]
            size = SIZES[layer]
            for y in range(size - 2):
                for x in range(size - 2):
                    count = self.model.NewIntVar(0, 8, f"n{layer}_{x}_{y}")
                    neighbors = [
                        source[y + dy][x + dx]
                        for dy in range(3)
                        for dx in range(3)
                        if (dx, dy) != (1, 1)
                    ]
                    self.model.Add(count == sum(neighbors))
                    self.model.AddAllowedAssignments(
                        [source[y + 1][x + 1], count, target[y][x]], allowed
                    )
        self.orbit_cells = []
        for orbit in range(len(ORBITS)):
            cells = []
            for layer, size in enumerate(SIZES):
                cells.extend(
                    self.layers[layer][y][x]
                    for y in range(size)
                    for x in range(size)
                    if POSITION_ORBIT[layer][x, y] == orbit
                )
            self.orbit_cells.append(cells)

    def maximize(self, weights, exact=False):
        if exact:
            scale = math.lcm(*(weight.denominator for weight in weights))
            coefficients = [int(weight * scale) for weight in weights]
        else:
            scale = 10_000_000
            coefficients = [round(float(weight) * scale) for weight in weights]
        self.model.Maximize(
            sum(
                coefficients[index] * sum(cells)
                for index, cells in enumerate(self.orbit_cells)
            )
        )
        solver = cp_model.CpSolver()
        solver.parameters.num_search_workers = 8
        solver.parameters.random_seed = 4
        status = solver.Solve(self.model)
        if status != cp_model.OPTIMAL:
            raise RuntimeError(f"separation failed: {solver.StatusName(status)}")
        counts = tuple(
            sum(solver.Value(cell) for cell in cells)
            for cells in self.orbit_cells
        )
        return sum(weight * count for weight, count in zip(weights, counts)), counts


def solve():
    rng = random.Random(4)
    columns = {
        count_vector(mask)
        for mask in (
            0,
            (1 << 36) - 1,
            *(rng.getrandbits(36) for _ in range(50)),
        )
    }
    separator = Separator()
    for iteration in range(200):
        matrix = np.array([list(column) + [-1] for column in columns], dtype=float)
        objective = np.zeros(len(ORBITS) + 1)
        objective[-1] = 1
        result = linprog(
            objective,
            A_ub=matrix,
            b_ub=np.zeros(len(columns)),
            A_eq=np.array([MULTIPLICITIES + [0]], dtype=float),
            b_eq=[1],
            bounds=[(0, None)] * len(ORBITS) + [(None, None)],
            method="highs",
        )
        if not result.success:
            raise RuntimeError(result.message)
        weights = [
            Fraction(float(value)).limit_denominator(1_000_000)
            for value in result.x[:-1]
        ]
        limit = Fraction(float(result.x[-1])).limit_denominator(1_000_000)
        score, column = separator.maximize(weights)
        print(
            json.dumps(
                {
                    "iteration": iteration,
                    "columns": len(columns),
                    "lp_limit": str(limit),
                    "separation": str(score),
                }
            ),
            flush=True,
        )
        if score <= limit:
            exact_score, _ = separator.maximize(weights, exact=True)
            if exact_score > limit:
                raise RuntimeError("rounded separation missed an exact violation")
            return weights, exact_score
        columns.add(column)
    raise RuntimeError("column generation did not converge")


def write_certificate(path, weights, maximum):
    scale = math.lcm(*(weight.denominator for weight in weights))
    integer_weights = [int(weight * scale) for weight in weights]
    lines = [
        "# Generated by pyramid_search.py.",
        f"total_weight {scale}",
        f"maximum_live_weight {int(maximum * scale)}",
    ]
    for layer, size in enumerate(SIZES):
        lines.append(f"layer {size} {size}")
        for y in range(size):
            lines.append(
                " ".join(
                    str(integer_weights[POSITION_ORBIT[layer][x, y]])
                    for x in range(size)
                )
            )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).with_name("pyramid_6x6.cert"),
    )
    args = parser.parse_args()
    weights, maximum = solve()
    write_certificate(args.output, weights, maximum)
    print(f"wrote {args.output}: bound {maximum}")


if __name__ == "__main__":
    main()
