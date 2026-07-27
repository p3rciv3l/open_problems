#!/usr/bin/env python3
"""Enumerate low-Hamming-weight assignments in the time-three Life cone."""

from __future__ import annotations

import argparse
import itertools
import math


def index(x: int, y: int, radius: int) -> int:
    return (y + radius) * (2 * radius + 1) + x + radius


def transition_masks(radius: int) -> list[tuple[int, int]]:
    masks = []
    for y in range(-radius + 1, radius):
        for x in range(-radius + 1, radius):
            mask = 0
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    if dx or dy:
                        mask |= 1 << index(x + dx, y + dy, radius)
            masks.append((mask, index(x, y, radius)))
    return masks


TIME_ONE_MASKS = transition_masks(3)
TIME_TWO_MASKS = transition_masks(2)


def step(state: int, masks: list[tuple[int, int]]) -> int:
    result = 0
    for output, (neighbor_mask, center) in enumerate(masks):
        neighbor_count = (state & neighbor_mask).bit_count()
        if neighbor_count == 3 or (
            neighbor_count == 2 and (state >> center) & 1
        ):
            result |= 1 << output
    return result


def origin_alive_at_time_three(initial: int) -> bool:
    time_two = step(step(initial, TIME_ONE_MASKS), TIME_TWO_MASKS)
    neighbors = (time_two & ~(1 << 4)).bit_count()
    return neighbors == 3 or (neighbors == 2 and bool((time_two >> 4) & 1))


def low_weight_counts(max_weight: int) -> list[int]:
    if isinstance(max_weight, bool) or not isinstance(max_weight, int):
        raise ValueError("max_weight must be an integer from 0 through 5")
    if not 0 <= max_weight <= 5:
        raise ValueError("max_weight must be an integer from 0 through 5")

    counts = []
    for weight in range(max_weight + 1):
        count = 0
        for live_cells in itertools.combinations(range(49), weight):
            state = sum(1 << cell for cell in live_cells)
            count += origin_alive_at_time_three(state)
        counts.append(count)
    return counts


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-weight", type=int, default=5)
    args = parser.parse_args()
    counts = low_weight_counts(args.max_weight)
    for weight, count in enumerate(counts):
        print(weight, math.comb(49, weight), count)


if __name__ == "__main__":
    main()
