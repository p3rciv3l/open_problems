#!/usr/bin/env python3
"""Column-generate the 6x10 shrinking-pyramid upper certificate."""

import argparse
import math
import random
import shutil
import subprocess
import tempfile
from fractions import Fraction
from pathlib import Path

import numpy as np
from scipy.optimize import linprog


HEIGHT = 10
DIMENSIONS = ((6, 10), (4, 8), (2, 6))
OFFSETS = (0, 15, 23)
ORBIT_COUNT = 26


def orbit(layer, x, y):
    width, height = DIMENSIONS[layer]
    return OFFSETS[layer] + min(x, width - 1 - x) + (width // 2) * min(
        y, height - 1 - y
    )


MULTIPLICITIES = [0] * ORBIT_COUNT
for layer, (width, height) in enumerate(DIMENSIONS):
    for y in range(height):
        for x in range(width):
            MULTIPLICITIES[orbit(layer, x, y)] += 1


def life_grid(grid):
    height, width = len(grid), len(grid[0])
    output = []
    for y in range(1, height - 1):
        row = []
        for x in range(1, width - 1):
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
        [(mask >> (x + 6 * y)) & 1 for x in range(6)] for y in range(HEIGHT)
    ]
    layers = [grid, life_grid(grid)]
    layers.append(life_grid(layers[-1]))
    counts = [0] * ORBIT_COUNT
    for layer, (width, height) in enumerate(DIMENSIONS):
        for y in range(height):
            for x in range(width):
                counts[orbit(layer, x, y)] += layers[layer][y][x]
    return tuple(counts)


class Separator:
    def __init__(self):
        compiler = shutil.which("g++")
        if not compiler:
            raise RuntimeError("g++ is required to build the exact separator")
        self.directory = tempfile.TemporaryDirectory()
        self.executable = Path(self.directory.name) / "separator"
        source = Path(__file__).with_name("strip_pyramid_separator.cpp")
        subprocess.run(
            [
                compiler,
                "-O3",
                "-std=c++17",
                str(source),
                "-o",
                str(self.executable),
            ],
            check=True,
        )

    def maximize(self, weights, exact=False):
        if exact:
            scale = math.lcm(*(weight.denominator for weight in weights))
            integers = [int(weight * scale) for weight in weights]
        else:
            scale = 10_000_000
            integers = [round(float(weight) * scale) for weight in weights]
        output = subprocess.check_output(
            [str(self.executable), str(HEIGHT), *(str(value) for value in integers)],
            text=True,
        )
        integer_score, mask = (int(value) for value in output.split())
        counts = count_vector(mask)
        if integer_score != sum(
            weight * count for weight, count in zip(integers, counts)
        ):
            raise RuntimeError("separator witness has the wrong score")
        score = sum(weight * count for weight, count in zip(weights, counts))
        return score, counts, mask


def solve():
    rng = random.Random(4)
    seeds = [
        0,
        (1 << (6 * HEIGHT)) - 1,
        *(rng.getrandbits(6 * HEIGHT) for _ in range(80)),
    ]
    columns = {count_vector(mask): mask for mask in seeds}
    separator = Separator()
    for iteration in range(300):
        column_list = list(columns)
        matrix = np.array(
            [list(column) + [-1] for column in column_list], dtype=float
        )
        objective = np.zeros(ORBIT_COUNT + 1)
        objective[-1] = 1
        result = linprog(
            objective,
            A_ub=matrix,
            b_ub=np.zeros(len(column_list)),
            A_eq=np.array([MULTIPLICITIES + [0]], dtype=float),
            b_eq=[1],
            bounds=[(0, None)] * ORBIT_COUNT + [(None, None)],
            method="highs",
        )
        if not result.success:
            raise RuntimeError(result.message)
        weights = list(result.x[:-1])
        limit = float(result.x[-1])
        score, column, mask = separator.maximize(weights)
        print(
            f"{iteration}: columns={len(columns)} "
            f"LP={limit} separation={score}",
            flush=True,
        )
        if score <= limit + 1e-8 or column in columns:
            weights = [Fraction(round(value * 1_000_000), 1_000_000) for value in weights]
            exact_score, _, _ = separator.maximize(weights, exact=True)
            limit = exact_score
            return weights, limit
        columns[column] = mask
    raise RuntimeError("column generation did not converge")


def write_certificate(path, weights, maximum):
    scale = math.lcm(*(weight.denominator for weight in weights))
    integers = [int(weight * scale) for weight in weights]
    total = sum(
        integers[orbit(layer, x, y)]
        for layer, (width, height) in enumerate(DIMENSIONS)
        for y in range(height)
        for x in range(width)
    )
    lines = [
        "# Generated by pyramid_6x10_search.py.",
        f"total_weight {total}",
        f"maximum_live_weight {int(maximum * scale)}",
    ]
    for layer, (width, height) in enumerate(DIMENSIONS):
        lines.append(f"layer {width} {height}")
        for y in range(height):
            lines.append(
                " ".join(
                    str(integers[orbit(layer, x, y)]) for x in range(width)
                )
            )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).with_name("pyramid_6x10.cert"),
    )
    args = parser.parse_args()
    weights, maximum = solve()
    write_certificate(args.output, weights, maximum)
    print(f"wrote {args.output}: verified bound {maximum}")


if __name__ == "__main__":
    main()
