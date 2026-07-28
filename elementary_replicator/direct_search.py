"""Independent explicit-state check of small clean-doubling scopes."""

import argparse
from dataclasses import dataclass
from itertools import combinations

from .life import Pattern, step, translate


@dataclass(frozen=True)
class DirectResult:
    seeds: int
    cases: int
    witnesses: tuple[tuple[int, int, int, Pattern, tuple[int, int]], ...]


def _canonical_seeds(width: int, height: int):
    for mask in range(1, 1 << (width * height)):
        seed = frozenset(
            (x, y)
            for y in range(height)
            for x in range(width)
            if (mask >> (y * width + x)) & 1
        )
        if (
            any(x == 0 for x, _ in seed)
            and any(x == width - 1 for x, _ in seed)
            and any(y == 0 for _, y in seed)
            and any(y == height - 1 for _, y in seed)
        ):
            yield seed


def _boxes_disjoint(a, b, width: int, height: int) -> bool:
    return (
        a[0] + width <= b[0]
        or b[0] + width <= a[0]
        or a[1] + height <= b[1]
        or b[1] + height <= a[1]
    )


def _doubling_offsets(
    seed: Pattern,
    terminal: Pattern,
    width: int,
    height: int,
):
    if len(terminal) != 2 * len(seed):
        return
    anchor = min(seed)
    candidates = []
    for x, y in terminal:
        offset = (x - anchor[0], y - anchor[1])
        copy = translate(seed, offset)
        if copy <= terminal:
            candidates.append((offset, copy))
    for (first, a), (second, b) in combinations(candidates, 2):
        if _boxes_disjoint(first, second, width, height) and a | b == terminal:
            yield first, second


def search(max_side: int, max_time: int) -> DirectResult:
    if max_side <= 0 or max_time <= 0:
        raise ValueError("max_side and max_time must be positive")
    seeds = 0
    cases = 0
    witnesses = []
    for width in range(1, max_side + 1):
        for height in range(1, width + 1):
            for seed in _canonical_seeds(width, height):
                seeds += 1
                current = seed
                for time in range(1, max_time + 1):
                    current = step(current)
                    cases += 1
                    for offsets in _doubling_offsets(
                        seed, current, width, height
                    ):
                        witnesses.append(
                            (width, height, time, seed, offsets)
                        )
    return DirectResult(seeds, cases, tuple(witnesses))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-side", type=int, default=3)
    parser.add_argument("--max-time", type=int, default=4)
    args = parser.parse_args()
    result = search(args.max_side, args.max_time)
    print(
        f"seeds={result.seeds} cases={result.cases} "
        f"witnesses={len(result.witnesses)}"
    )
    for witness in result.witnesses:
        print(witness)


if __name__ == "__main__":
    main()
