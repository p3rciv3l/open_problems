#!/usr/bin/env python3
"""Solve and rationalize the two-center spacetime-strip LP."""

import argparse
import json
from fractions import Fraction
from pathlib import Path

import numpy as np
from scipy.optimize import linprog
from scipy.sparse import coo_matrix

from strip2_model import PATTERN_COUNT, tile_data
from strip2_verify import verify


X_FACE_COUNT = 1024
Y_FACE_COUNT = 256
TIME_FACE_COUNT = 4
VARIABLE_COUNT = 1 + X_FACE_COUNT + Y_FACE_COUNT + TIME_FACE_COUNT
GRID_DENOMINATOR = 10_000


def build_lp():
    rows = []
    columns = []
    values = []
    rhs = np.empty(PATTERN_COUNT)
    for mask in range(PATTERN_COUNT):
        center_sum, current, nxt, left, right, top, bottom, _ = tile_data(mask)
        rhs[mask] = -center_sum
        terms = (
            (0, -1),
            (1 + left, -1),
            (1 + right, 1),
            (1 + X_FACE_COUNT + top, -1),
            (1 + X_FACE_COUNT + bottom, 1),
            (1 + X_FACE_COUNT + Y_FACE_COUNT + current, -1),
            (1 + X_FACE_COUNT + Y_FACE_COUNT + nxt, 1),
        )
        for column, value in terms:
            rows.append(mask)
            columns.append(column)
            values.append(value)
    matrix = coo_matrix(
        (values, (rows, columns)), shape=(PATTERN_COUNT, VARIABLE_COUNT)
    ).tocsr()
    objective = np.zeros(VARIABLE_COUNT)
    objective[0] = 1
    return matrix, rhs, objective


def grid(value: float) -> Fraction:
    return Fraction(round(float(value) * GRID_DENOMINATOR), GRID_DENOMINATOR)


def solve() -> dict:
    matrix, rhs, objective = build_lp()
    result = linprog(
        objective,
        A_ub=matrix,
        b_ub=rhs,
        bounds=[(None, None)] * VARIABLE_COUNT,
        method="highs",
    )
    if not result.success:
        raise RuntimeError(result.message)

    potentials = [grid(value) for value in result.x[1:]]
    block_constant = max(
        Fraction(-int(rhs[mask]))
        + sum(
            Fraction(int(matrix[mask, column])) * potentials[column - 1]
            for column in matrix[mask].indices
            if column
        )
        for mask in range(PATTERN_COUNT)
    )
    dual = {
        str(mask): str(Fraction(float(-value)).limit_denominator(1000))
        for mask, value in enumerate(result.ineqlin.marginals)
        if value < -1e-9
    }
    certificate = {
        "format": 1,
        "model": "B3/S23 4x3-to-two-centers two-time-slice full-face LP",
        "block_constant": str(block_constant),
        "density_bound": str(block_constant / 2),
        "lp_density_lower_bound": "3/5",
        "rationalization_grid": GRID_DENOMINATOR,
        "potentials": {
            "x_spacetime_face": [
                str(value) for value in potentials[:X_FACE_COUNT]
            ],
            "y_face": [
                str(value)
                for value in potentials[
                    X_FACE_COUNT : X_FACE_COUNT + Y_FACE_COUNT
                ]
            ],
            "time_pair": [
                str(value) for value in potentials[X_FACE_COUNT + Y_FACE_COUNT :]
            ],
        },
        "lp_lower_witness": dual,
    }
    verify(certificate)
    return certificate


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).with_name("strip2_certificate.json"),
    )
    args = parser.parse_args()
    certificate = solve()
    args.output.write_text(
        json.dumps(certificate, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(
        f"wrote {args.output}: density <= {certificate['density_bound']}; "
        f"LP density >= {certificate['lp_density_lower_bound']}"
    )


if __name__ == "__main__":
    main()
