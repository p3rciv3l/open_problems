from __future__ import annotations

import argparse
import json
from pathlib import Path

from .transfer import Background, TransferSearch, TransferSpec


def main() -> int:
    here = Path(__file__).parent
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--background",
        type=Path,
        default=here / "backgrounds" / "block_lattice_6x4.json",
    )
    parser.add_argument("--max-column-deviations", type=int, default=2)
    parser.add_argument("--width", type=int, default=4)
    parser.add_argument(
        "--output",
        type=Path,
        default=here / "results" / "isolated_block6x4_k2.json",
    )
    args = parser.parse_args()
    search = TransferSearch(
        TransferSpec(
            width=args.width,
            max_column_deviations=args.max_column_deviations,
        ),
        Background.load(args.background),
    )
    result = search.search()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(
        f"{result['status']}: {result['reachable_states']} states, "
        f"{result['reachable_edges']} edges -> {args.output}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
