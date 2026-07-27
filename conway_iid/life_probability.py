#!/usr/bin/env python3
"""Exact finite-time one-site probabilities for Conway's Game of Life."""

from __future__ import annotations

import argparse
import json
import math
import random
from functools import lru_cache
from typing import Iterable, Sequence

Coordinate = tuple[int, int]


def square(radius: int) -> list[Coordinate]:
    return [
        (x, y)
        for y in range(-radius, radius + 1)
        for x in range(-radius, radius + 1)
    ]


def neighbors(cell: Coordinate) -> list[Coordinate]:
    x, y = cell
    return [
        (x + dx, y + dy)
        for dy in (-1, 0, 1)
        for dx in (-1, 0, 1)
        if dx or dy
    ]


class BDD:
    """A small reduced ordered BDD with exact weight enumeration."""

    def __init__(self, variable_count: int):
        self.variable_count = variable_count
        # Terminals use variable_count as their level.
        self.nodes: list[tuple[int, int, int]] = [
            (variable_count, 0, 0),
            (variable_count, 1, 1),
        ]
        self.unique: dict[tuple[int, int, int], int] = {}
        self._apply_cache: dict[tuple[str, int, int], int] = {}
        self._not_cache: dict[int, int] = {0: 1, 1: 0}

    def make(self, variable: int, low: int, high: int) -> int:
        if low == high:
            return low
        key = (variable, low, high)
        result = self.unique.get(key)
        if result is None:
            result = len(self.nodes)
            self.unique[key] = result
            self.nodes.append(key)
        return result

    def variable(self, index: int) -> int:
        return self.make(index, 0, 1)

    def negate(self, node: int) -> int:
        cached = self._not_cache.get(node)
        if cached is not None:
            return cached
        variable, low, high = self.nodes[node]
        result = self.make(variable, self.negate(low), self.negate(high))
        self._not_cache[node] = result
        return result

    def apply(self, operator: str, left: int, right: int) -> int:
        if left > right:
            left, right = right, left
        key = (operator, left, right)
        cached = self._apply_cache.get(key)
        if cached is not None:
            return cached

        if operator == "and":
            if left == 0:
                return 0
            if left == 1:
                return right
            if left == right:
                return left
        elif operator == "or":
            if right == 1:
                return 1
            if left == 0:
                return right
            if left == right:
                return left
        else:
            raise ValueError(f"unknown operator: {operator}")

        left_variable = self.nodes[left][0]
        right_variable = self.nodes[right][0]
        variable = min(left_variable, right_variable)
        left_low, left_high = (
            self.nodes[left][1:] if left_variable == variable else (left, left)
        )
        right_low, right_high = (
            self.nodes[right][1:] if right_variable == variable else (right, right)
        )
        result = self.make(
            variable,
            self.apply(operator, left_low, right_low),
            self.apply(operator, left_high, right_high),
        )
        self._apply_cache[key] = result
        return result

    def exactly(self, functions: Iterable[int], target: int) -> int:
        counts = [1] + [0] * target
        for function in functions:
            complement = self.negate(function)
            counts = [
                self.apply(
                    "or",
                    self.apply("and", counts[count], complement),
                    self.apply("and", counts[count - 1], function) if count else 0,
                )
                for count in range(target + 1)
            ]
        return counts[target]

    def life(self, alive: int, neighbor_functions: Sequence[int]) -> int:
        exactly_two = self.exactly(neighbor_functions, 2)
        exactly_three = self.exactly(neighbor_functions, 3)
        return self.apply(
            "or", self.apply("and", alive, exactly_two), exactly_three
        )

    def weight_counts(self, root: int) -> list[int]:
        """Count satisfying assignments by the number of true variables."""

        @lru_cache(maxsize=None)
        def visit(node: int, level: int) -> tuple[int, ...]:
            remaining = self.variable_count - level
            if node == 0:
                return (0,) * (remaining + 1)
            if node == 1:
                return tuple(math.comb(remaining, weight) for weight in range(remaining + 1))

            variable, low, high = self.nodes[node]
            gap = variable - level
            low_counts = visit(low, variable + 1)
            high_counts = visit(high, variable + 1)
            result = [0] * (remaining + 1)
            for gap_weight in range(gap + 1):
                multiplier = math.comb(gap, gap_weight)
                for weight, count in enumerate(low_counts):
                    result[gap_weight + weight] += multiplier * count
                for weight, count in enumerate(high_counts):
                    result[gap_weight + weight + 1] += multiplier * count
            return tuple(result)

        return list(visit(root, 0))


def bernstein_to_power(counts: Sequence[int]) -> list[int]:
    """Expand sum counts[k] p^k (1-p)^(n-k) in the power basis."""
    degree = len(counts) - 1
    coefficients = [0] * (degree + 1)
    for weight, count in enumerate(counts):
        for extra in range(degree - weight + 1):
            coefficients[weight + extra] += (
                count * math.comb(degree - weight, extra) * (-1) ** extra
            )
    while len(coefficients) > 1 and coefficients[-1] == 0:
        coefficients.pop()
    return coefficients


def exact_probability(time: int) -> dict[str, object]:
    if time < 0:
        raise ValueError("time must be nonnegative")
    if time > 2:
        raise ValueError("exact construction is currently limited to time <= 2")

    cells = square(time)
    index = {cell: position for position, cell in enumerate(cells)}
    bdd = BDD(len(cells))
    generation = {cell: bdd.variable(index[cell]) for cell in cells}
    for step in range(time):
        next_radius = time - step - 1
        generation = {
            cell: bdd.life(generation[cell], [generation[n] for n in neighbors(cell)])
            for cell in square(next_radius)
        }

    counts = bdd.weight_counts(generation[(0, 0)])
    return {
        "time": time,
        "variables": len(cells),
        "bdd_nodes": len(bdd.nodes),
        "weight_counts": counts,
        "power_coefficients": bernstein_to_power(counts),
    }


def evaluate_power(coefficients: Sequence[int], p: float) -> float:
    result = 0.0
    for coefficient in reversed(coefficients):
        result = result * p + coefficient
    return result


def simulate_once(time: int, p: float, rng: random.Random) -> bool:
    cells = {cell: rng.random() < p for cell in square(time)}
    for step in range(time):
        radius = time - step - 1
        next_cells = {}
        for cell in square(radius):
            neighbor_count = sum(cells[n] for n in neighbors(cell))
            next_cells[cell] = neighbor_count == 3 or (
                cells[cell] and neighbor_count == 2
            )
        cells = next_cells
    return cells[(0, 0)]


def monte_carlo(time: int, p: float, trials: int, seed: int) -> float:
    if isinstance(trials, bool) or not isinstance(trials, int) or trials <= 0:
        raise ValueError("trials must be a positive integer")
    rng = random.Random(seed)
    return sum(simulate_once(time, p, rng) for _ in range(trials)) / trials


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("time", type=int, choices=range(3))
    parser.add_argument("--monte-carlo", type=int, metavar="TRIALS")
    parser.add_argument("--p", type=float, default=0.3)
    parser.add_argument("--seed", type=int, default=1)
    args = parser.parse_args()

    result = exact_probability(args.time)
    if args.monte_carlo is not None:
        result["evaluation"] = evaluate_power(result["power_coefficients"], args.p)
        result["monte_carlo"] = monte_carlo(
            args.time, args.p, args.monte_carlo, args.seed
        )
        result["p"] = args.p
        result["trials"] = args.monte_carlo
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
