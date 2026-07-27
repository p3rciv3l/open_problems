from __future__ import annotations

import argparse
import json
from pathlib import Path

from .pattern import PeriodicPattern, Window
from .sat import enumerate_margins
from .verify import verify_witness


def _load_tile(path: str, name: str | None) -> PeriodicPattern:
    rows = tuple(
        line.strip()
        for line in Path(path).read_text().splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    )
    return PeriodicPattern(rows, name or Path(path).stem)


def main() -> int:
    parser = argparse.ArgumentParser(description="Finite stabilization of periodic Life still lifes")
    subparsers = parser.add_subparsers(dest="command", required=True)
    enumerate_parser = subparsers.add_parser("enumerate")
    enumerate_parser.add_argument("--tile", required=True)
    enumerate_parser.add_argument("--name")
    enumerate_parser.add_argument("--origin", nargs=2, type=int, default=(0, 0), metavar=("X", "Y"))
    enumerate_parser.add_argument("--size", nargs=2, type=int, required=True, metavar=("W", "H"))
    enumerate_parser.add_argument("--max-margin", type=int, required=True)
    enumerate_parser.add_argument("--solver", default="cadical195")
    enumerate_parser.add_argument("--output", required=True)

    verify_parser = subparsers.add_parser("verify")
    verify_parser.add_argument("witness")
    args = parser.parse_args()

    if args.command == "enumerate":
        pattern = _load_tile(args.tile, args.name)
        window = Window(*args.origin, *args.size)
        result = enumerate_margins(pattern, window, args.max_margin, args.solver)
        Path(args.output).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
        print(
            f"minimum margin: {result['minimum_margin']}"
            if result["minimum_margin"] is not None
            else f"UNSAT through margin {result['searched_through']}"
        )
        return 0

    data = json.loads(Path(args.witness).read_text())
    if data.get("format") == "still-life-finitization-experiments-v1":
        witnesses = [case.get("witness") for case in data["cases"]]
    elif data.get("format") == "still-life-finitization-result-v1":
        witnesses = [data.get("witness")]
    elif data.get("format") == "still-life-finitization-witness-v1":
        witnesses = [data]
    else:
        print("unrecognized witness format")
        return 2
    if any(witness is None for witness in witnesses):
        print("input contains a result without a witness")
        return 2
    for index, witness in enumerate(witnesses):
        errors = verify_witness(witness)
        if errors:
            prefix = f"witness {index}: " if len(witnesses) > 1 else ""
            print("\n".join(prefix + error for error in errors))
            return 1
    print(f"{len(witnesses)} witness(es) verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
