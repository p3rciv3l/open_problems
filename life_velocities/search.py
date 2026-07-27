from __future__ import annotations

import argparse
import json
from pathlib import Path

from .model import SearchSpec, WaveModel
from .simulate import verify_witness


def _range(text: str) -> list[int]:
    start, end = (int(value) for value in text.split(":", 1))
    if start <= 0 or end < start:
        raise argparse.ArgumentTypeError("range must be positive START:END")
    return list(range(start, end + 1))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--lengths", type=_range, default=[8])
    parser.add_argument("--widths", type=_range, default=[3])
    parser.add_argument("--seam-phase", type=int, default=0)
    parser.add_argument("--background-period", type=int, default=1)
    parser.add_argument("--background-x-period", type=int, default=4)
    parser.add_argument("--background-y-period", type=int, default=4)
    parser.add_argument("--background-phase", type=int, default=0)
    parser.add_argument("--guard-columns", type=int, default=1)
    parser.add_argument("--allow-dead-background", action="store_true")
    parser.add_argument("--allow-stationary", action="store_true")
    parser.add_argument("--timeout-ms", type=int, default=60_000)
    parser.add_argument("--output", type=Path, default=Path("results"))
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)

    for width in args.widths:
        for length in args.lengths:
            spec = SearchSpec(
                length=length,
                width=width,
                seam_phase=args.seam_phase,
                background_period=args.background_period,
                background_x_period=args.background_x_period,
                background_y_period=args.background_y_period,
                background_phase=args.background_phase,
                guard_columns=args.guard_columns,
                require_live_background=not args.allow_dead_background,
                require_motion=not args.allow_stationary,
            )
            result = WaveModel(spec).solve(args.timeout_ms)
            if result["status"] == "sat":
                errors = verify_witness(result)
                result["independent_verification"] = {
                    "status": "pass" if not errors else "fail",
                    "errors": errors,
                }
                if errors:
                    raise RuntimeError(errors[0])
            path = args.output / f"L{length}_W{width}_S{args.seam_phase}.json"
            path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
            print(f"{length}x{width}: {result['status']} -> {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
