#!/usr/bin/env python3
"""Small, dependency-free semantic checker for the attaining witness."""

import json
import sys
from pathlib import Path

N = 4


def step(state):
    result = set()
    for row in range(N):
        for col in range(N):
            neighbors = sum(
                ((row + dr) % N, (col + dc) % N) in state
                for dr in (-1, 0, 1)
                for dc in (-1, 0, 1)
                if (dr, dc) != (0, 0)
            )
            if neighbors == 3 or ((row, col) in state and neighbors == 2):
                result.add((row, col))
    return result


def main(path):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    assert data["rule"] == "B3/S23"
    assert data["topology"] == "4x4_torus"
    assert data["period"] == 2
    states = [{tuple(cell) for cell in state} for state in data["states"]]
    assert len(states) == 2 and states[0] != states[1]
    assert len(states[0]) == data["population_time_0"] == 3
    assert step(states[0]) == states[1]
    assert step(states[1]) == states[0]
    print("witness OK: exact period 2, time-0 population 3")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) == 2 else Path(__file__).parents[1] / "artifacts/witness.json")
