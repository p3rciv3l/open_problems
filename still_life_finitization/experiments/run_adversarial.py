from __future__ import annotations

import json
import platform
from pathlib import Path

import pysat

from ..still_life import PeriodicPattern, Window, enumerate_margins


FAMILIES = (
    (
        "beehive-square-cut",
        PeriodicPattern((".11...", "1..1..", ".11...", "......", "......"), "beehive-6x5"),
        (5, 4),
    ),
    (
        "loaf-square-cut",
        PeriodicPattern(
            (".11...", "1..1..", ".1.1..", "..1...", "......", "......"),
            "loaf-6x6",
        ),
        (5, 3),
    ),
    (
        "pond-square-cut",
        PeriodicPattern(
            (".11...", "1..1..", "1..1..", ".11...", "......", "......"),
            "pond-6x6",
        ),
        (5, 5),
    ),
)

STRIPES = PeriodicPattern(("1", "."), "alternating-live-rows")


def main() -> None:
    records = []
    for family, pattern, origin in FAMILIES:
        for side in range(1, 17):
            print(f"{family}: {side}x{side}")
            result = enumerate_margins(
                pattern, Window(*origin, side, side), max_margin=4
            )
            records.append({"family": family, **result})
    for width in range(1, 33):
        family = "alternating-live-rows-height-1"
        print(f"{family}: {width}x1")
        result = enumerate_margins(
            STRIPES, Window(0, 0, width, 1), max_margin=4
        )
        records.append({"family": family, **result})
    output = {
        "format": "still-life-finitization-adversarial-v1",
        "solver": "cadical195",
        "python": platform.python_version(),
        "python_sat": pysat.__version__,
        "case_count": len(records),
        "cases": records,
    }
    Path(__file__).with_name("adversarial_results.json").write_text(
        json.dumps(output, indent=2, sort_keys=True) + "\n"
    )


if __name__ == "__main__":
    main()
