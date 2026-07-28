from __future__ import annotations

import argparse
import json
import platform
from pathlib import Path

import pysat

from ..still_life import PeriodicPattern, Window, enumerate_margins


BLOCK = PeriodicPattern(("11..", "11..", "....", "...."), "block-4x4")
TUB = PeriodicPattern((".1...", "1.1..", ".1...", ".....", "....."), "tub-5x5")


def cases():
    for size in range(1, 13):
        yield "block-aligned-squares", BLOCK, Window(0, 0, size, size)
        yield "block-shifted-squares", BLOCK, Window(1, 1, size, size)
        yield "tub-aligned-squares", TUB, Window(0, 0, size, size)
        yield "tub-dead-phase-squares", TUB, Window(2, 2, size, size)
    for width in range(1, 17):
        yield "tub-height-1-strips", TUB, Window(0, 0, width, 1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Reproduce controlled margin experiments")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).with_name("results.json"),
    )
    parser.add_argument("--max-cases", type=int, help=argparse.SUPPRESS)
    args = parser.parse_args()

    records = []
    selected_cases = cases()
    if args.max_cases is not None:
        if args.max_cases < 0:
            parser.error("--max-cases must be nonnegative")
        import itertools

        selected_cases = itertools.islice(selected_cases, args.max_cases)
    for family, pattern, window in selected_cases:
        print(f"{family}: {window.width}x{window.height}")
        result = enumerate_margins(pattern, window, max_margin=4)
        records.append({"family": family, **result})

    output = {
        "format": "still-life-finitization-experiments-v1",
        "solver": "cadical195",
        "python": platform.python_version(),
        "python_sat": pysat.__version__,
        "case_count": len(records),
        "cases": records,
    }
    args.output.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
