#!/usr/bin/env python3
"""Dependency-free checks for the protected-blinker cylinder argument."""

from __future__ import annotations

import argparse

Cell = tuple[int, int]
BLINKER = {(-1, 0), (0, 0), (1, 0)}
ARM = (1, 0)


def cylinder_exponent(horizon: int) -> int:
    if horizon < 0:
        raise ValueError("horizon must be nonnegative")
    radius = horizon + 2
    return (2 * radius + 1) ** 2 - len(BLINKER)


def cylinder_probability(horizon: int, p):
    return p**len(BLINKER) * (1 - p) ** cylinder_exponent(horizon)


def next_generation(live: set[Cell]) -> set[Cell]:
    neighbor_counts: dict[Cell, int] = {}
    for x, y in live:
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                if dx or dy:
                    cell = (x + dx, y + dy)
                    neighbor_counts[cell] = neighbor_counts.get(cell, 0) + 1
    return {
        cell
        for cell, count in neighbor_counts.items()
        if count == 3 or (count == 2 and cell in live)
    }


def verify_horizon(horizon: int) -> None:
    if horizon < 0:
        raise ValueError("horizon must be nonnegative")
    radius = horizon + 2

    for step in range(horizon + 2):
        for y in range(ARM[1] - step, ARM[1] + step + 1):
            for x in range(ARM[0] - step, ARM[0] + step + 1):
                assert max(abs(x), abs(y)) <= radius

    live = set(BLINKER)
    for step in range(horizon + 2):
        assert (ARM in live) == (step % 2 == 0)
        live = next_generation(live)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-horizon", type=int, default=20)
    args = parser.parse_args()
    for horizon in range(args.max_horizon + 1):
        verify_horizon(horizon)
    print(f"verified protected blinker for horizons 0..{args.max_horizon}")


if __name__ == "__main__":
    main()
