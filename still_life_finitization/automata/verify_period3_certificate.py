from __future__ import annotations

import argparse
import json
from pathlib import Path

from ..still_life.period3_transfer import verify_period3_certificate


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "certificate",
        nargs="?",
        type=Path,
        default=Path(__file__).with_name("period3_certificate.json"),
    )
    args = parser.parse_args()
    errors = verify_period3_certificate(json.loads(args.certificate.read_text()))
    if errors:
        raise SystemExit("\n".join(errors))
    print("period-3 certificate verified")


if __name__ == "__main__":
    main()
