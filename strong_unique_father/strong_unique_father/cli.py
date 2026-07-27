from __future__ import annotations

import argparse
import json
from pathlib import Path

from .forcing import analyze_stabilization
from .patterns import STABILIZATION_334


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    parser.add_argument("--independent", action="store_true")
    args = parser.parse_args()
    report = analyze_stabilization(STABILIZATION_334, independent=args.independent)
    serialized = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(serialized)
    else:
        print(serialized, end="")


if __name__ == "__main__":
    main()
