from __future__ import annotations

import argparse
import json
from pathlib import Path

from .transfer import Background, TransferSearch, TransferSpec


def verify_result(result_path: Path, background_path: Path) -> list[str]:
    recorded = json.loads(result_path.read_text())
    if recorded.get("format") != "life_velocities.isolated_transfer.v1":
        return ["unsupported result format"]
    spec = TransferSpec(**recorded["spec"])
    reproduced = TransferSearch(spec, Background.load(background_path)).search()
    if reproduced != recorded:
        fields = sorted(
            key
            for key in set(reproduced) | set(recorded)
            if reproduced.get(key) != recorded.get(key)
        )
        return [f"reproduced result differs in: {', '.join(fields)}"]
    return []


def main() -> int:
    here = Path(__file__).parent
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "result",
        type=Path,
        nargs="?",
        default=here / "results" / "isolated_block6x4_k1.json",
    )
    parser.add_argument(
        "--background",
        type=Path,
        default=here / "backgrounds" / "block_lattice_6x4.json",
    )
    args = parser.parse_args()
    errors = verify_result(args.result, args.background)
    if errors:
        for error in errors:
            print(error)
        return 1
    print(f"verified exact reproduction: {args.result}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
