from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .optimizer import optimize
from .verify import verify_result


def _positive_int(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be positive")
    return parsed


def _csv_ints(value: str) -> list[int]:
    try:
        values = [int(item) for item in value.split(",")]
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be comma-separated integers") from exc
    if not values or any(item <= 0 for item in values):
        raise argparse.ArgumentTypeError("all values must be positive")
    return values


def _write_json(data: Any, output: str | None) -> None:
    text = json.dumps(data, indent=2, sort_keys=True) + "\n"
    if output:
        Path(output).parent.mkdir(parents=True, exist_ok=True)
        Path(output).write_text(text, encoding="utf-8")
    else:
        print(text, end="")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="life-density")
    commands = parser.add_subparsers(dest="command", required=True)

    solve = commands.add_parser("optimize", help="solve one W x H, P instance")
    solve.add_argument("width", type=_positive_int)
    solve.add_argument("height", type=_positive_int)
    solve.add_argument("period", type=_positive_int)
    solve.add_argument("--exact-period", action="store_true")
    solve.add_argument("--timeout", type=float)
    solve.add_argument("--seed", type=int, default=0)
    solve.add_argument("-o", "--output")

    verify = commands.add_parser("verify", help="independently simulate a result JSON")
    verify.add_argument("result")

    grid = commands.add_parser("grid", help="solve a Cartesian product of instances")
    grid.add_argument("--widths", required=True, type=_csv_ints)
    grid.add_argument("--heights", required=True, type=_csv_ints)
    grid.add_argument("--periods", required=True, type=_csv_ints)
    grid.add_argument("--exact-period", action="store_true")
    grid.add_argument("--timeout", type=float)
    grid.add_argument("--seed", type=int, default=0)
    grid.add_argument("-o", "--output")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.command == "optimize":
        result = optimize(
            args.width,
            args.height,
            args.period,
            exact_period=args.exact_period,
            timeout_seconds=args.timeout,
            seed=args.seed,
        )
        _write_json(result, args.output)
        return 0 if result["status"] in {"optimal", "unsat"} else 2
    if args.command == "verify":
        result = json.loads(Path(args.result).read_text(encoding="utf-8"))
        report = verify_result(result)
        _write_json(report, None)
        return 0 if report["valid"] else 1

    results = [
        optimize(
            width,
            height,
            period,
            exact_period=args.exact_period,
            timeout_seconds=args.timeout,
            seed=args.seed,
        )
        for width in args.widths
        for height in args.heights
        for period in args.periods
    ]
    artifact = {"schema": "life-density-grid/v1", "results": results}
    _write_json(artifact, args.output)
    return 0 if all(result["status"] in {"optimal", "unsat"} for result in results) else 2


if __name__ == "__main__":
    raise SystemExit(main())

