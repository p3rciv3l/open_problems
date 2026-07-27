from __future__ import annotations

import argparse
import json
from pathlib import Path

from .forcing import analyze_stabilization
from .patterns import (
    KYNNOES_BOUNDARY_OBSTRUCTION,
    STABILIZATION_334,
    STABILIZATION_710,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    parser.add_argument("--independent", action="store_true")
    parser.add_argument("--annulus", type=int, default=2)
    parser.add_argument("--candidate", choices=("334", "710"), default="710")
    args = parser.parse_args()
    pattern = STABILIZATION_334 if args.candidate == "334" else STABILIZATION_710
    report = analyze_stabilization(
        pattern, independent=args.independent, output_annulus=args.annulus
    )
    if args.candidate == "710":
        report["exact_global_counter_predecessor"] = {
            "construction": "stabilization_live_cells symmetric_difference toggled_cells",
            "toggled_cells": [list(cell) for cell in sorted(KYNNOES_BOUNDARY_OBSTRUCTION)],
            "missing_target_live_cell": [8, 0],
            "applies_to_all_equal_xy_expansions": True,
        }
    serialized = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(serialized)
    else:
        print(serialized, end="")


if __name__ == "__main__":
    main()
