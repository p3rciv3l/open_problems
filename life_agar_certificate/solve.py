#!/usr/bin/env python3
"""Solve the radius-one local-certificate LP and emit exact rational data."""

import argparse
import json
from fractions import Fraction
from pathlib import Path

import numpy as np
from scipy.optimize import linprog
from scipy.sparse import coo_matrix

from model import tile_data
from verify import verify


FACE_COUNT = 64
VARIABLE_COUNT = 1 + 2 * FACE_COUNT + 2


def build_lp():
    rows = []
    columns = []
    values = []
    rhs = np.empty(512)
    for mask in range(512):
        center, nxt, left, right, top, bottom = tile_data(mask)
        rhs[mask] = -center
        terms = (
            (0, -1),
            (1 + left, -1),
            (1 + right, 1),
            (1 + FACE_COUNT + top, -1),
            (1 + FACE_COUNT + bottom, 1),
            (1 + 2 * FACE_COUNT + center, -1),
            (1 + 2 * FACE_COUNT + nxt, 1),
        )
        for column, value in terms:
            rows.append(mask)
            columns.append(column)
            values.append(value)
    matrix = coo_matrix(
        (values, (rows, columns)), shape=(512, VARIABLE_COUNT)
    ).tocsr()
    objective = np.zeros(VARIABLE_COUNT)
    objective[0] = 1
    return matrix, rhs, objective


def rational(value: float) -> Fraction:
    return Fraction(float(value)).limit_denominator(1_000_000)


def text(value: Fraction) -> str:
    return str(value)


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

    weights = [rational(value) for value in result.x]
    dual = {
        str(mask): text(rational(-value))
        for mask, value in enumerate(result.ineqlin.marginals)
        if value < -1e-9
    }
    certificate = {
        "format": 1,
        "model": "B3/S23 radius-1 3x3-to-center full-face LP",
        "bound": text(weights[0]),
        "potentials": {
            "x_face": [text(value) for value in weights[1:65]],
            "y_face": [text(value) for value in weights[65:129]],
            "time_cell": [text(value) for value in weights[129:131]],
        },
        "optimality_witness": dual,
    }
    verify(certificate)
    return certificate


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).with_name("certificate.json"),
    )
    args = parser.parse_args()
    certificate = solve()
    args.output.write_text(
        json.dumps(certificate, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(f"wrote {args.output}: exact optimum {certificate['bound']}")


if __name__ == "__main__":
    main()
