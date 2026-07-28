#!/usr/bin/env python3
"""Search locally translation-consistent Life spacetime cluster LPs."""

import argparse
from fractions import Fraction

import numpy as np
from scipy.optimize import linprog
from scipy.sparse import coo_matrix


def bit(mask: int, width: int, x: int, y: int) -> int:
    return (mask >> (x + width * y)) & 1


def encode(values) -> int:
    return sum(value << index for index, value in enumerate(values))


def life_output(mask: int, width: int, x: int, y: int) -> int:
    center = bit(mask, width, x, y)
    neighbors = sum(
        bit(mask, width, x + dx, y + dy)
        for dy in (-1, 0, 1)
        for dx in (-1, 0, 1)
        if dx or dy
    )
    return int(neighbors == 3 or (center and neighbors == 2))


def input_code(mask: int, width: int, xs, ys) -> int:
    return encode(bit(mask, width, x, y) for y in ys for x in xs)


def output_code(mask: int, width: int, xs, ys) -> int:
    return encode(life_output(mask, width, x, y) for y in ys for x in xs)


def face_codes(mask: int, width: int, height: int) -> tuple[int, int, int, int]:
    left_values = [
        bit(mask, width, x, y)
        for y in range(height)
        for x in range(width - 1)
    ]
    right_values = [
        bit(mask, width, x, y)
        for y in range(height)
        for x in range(1, width)
    ]
    left_values += [
        life_output(mask, width, x, y)
        for y in range(1, height - 1)
        for x in range(1, width - 2)
    ]
    right_values += [
        life_output(mask, width, x, y)
        for y in range(1, height - 1)
        for x in range(2, width - 1)
    ]
    top_values = [
        bit(mask, width, x, y)
        for y in range(height - 1)
        for x in range(width)
    ]
    bottom_values = [
        bit(mask, width, x, y)
        for y in range(1, height)
        for x in range(width)
    ]
    top_values += [
        life_output(mask, width, x, y)
        for y in range(1, height - 2)
        for x in range(1, width - 1)
    ]
    bottom_values += [
        life_output(mask, width, x, y)
        for y in range(2, height - 1)
        for x in range(1, width - 1)
    ]
    return tuple(map(encode, (left_values, right_values, top_values, bottom_values)))


def solve(width: int, height: int):
    if width < 3 or height < 3:
        raise ValueError("clusters must be at least 3 x 3")
    pattern_count = 1 << (width * height)
    rows = []
    columns = []
    values = []
    row_offset = 0

    def add_balance(codes, code_count):
        nonlocal row_offset
        for mask, (source, target) in enumerate(codes):
            if source != target:
                rows.extend((row_offset + source, row_offset + target))
                columns.extend((mask, mask))
                values.extend((1, -1))
        row_offset += code_count

    faces = [face_codes(mask, width, height) for mask in range(pattern_count)]
    x_bits = (width - 1) * height + max(width - 3, 0) * (height - 2)
    y_bits = width * (height - 1) + (width - 2) * max(height - 3, 0)
    add_balance(((left, right) for left, right, _, _ in faces), 1 << x_bits)
    add_balance(((top, bottom) for _, _, top, bottom in faces), 1 << y_bits)

    interior = range(1, width - 1), range(1, height - 1)
    add_balance(
        (
            (
                input_code(mask, width, *interior),
                output_code(mask, width, *interior),
            )
            for mask in range(pattern_count)
        ),
        1 << ((width - 2) * (height - 2)),
    )
    rows.extend([row_offset] * pattern_count)
    columns.extend(range(pattern_count))
    values.extend([1] * pattern_count)
    rhs = np.zeros(row_offset + 1)
    rhs[row_offset] = 1
    matrix = coo_matrix(
        (values, (rows, columns)), shape=(row_offset + 1, pattern_count)
    ).tocsr()
    objective = -np.array(
        [bit(mask, width, 1, 1) for mask in range(pattern_count)], dtype=float
    )
    result = linprog(
        objective,
        A_eq=matrix,
        b_eq=rhs,
        bounds=(0, None),
        method="highs-ipm",
    )
    if not result.success:
        raise RuntimeError(result.message)
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "levels",
        nargs="*",
        default=["3x3", "4x3", "4x4"],
        help="input-window dimensions, for example 4x4",
    )
    args = parser.parse_args()
    for level in args.levels:
        width, height = map(int, level.lower().split("x"))
        result = solve(width, height)
        value = Fraction(-result.fun).limit_denominator(1_000_000)
        support = sum(weight > 1e-8 for weight in result.x)
        print(f"{width}x{height}: {value} support={support}")


if __name__ == "__main__":
    main()
