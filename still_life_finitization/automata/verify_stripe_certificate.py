from __future__ import annotations

import argparse
import json
from pathlib import Path

from ..still_life.stripe_transfer import verify_stripe_certificate


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify alternating-row pump certificate")
    parser.add_argument(
        "certificate",
        nargs="?",
        type=Path,
        default=Path(__file__).with_name("alternating_rows_certificate.json"),
    )
    args = parser.parse_args()
    errors = verify_stripe_certificate(json.loads(args.certificate.read_text()))
    if errors:
        print("\n".join(errors))
        return 1
    print("alternating-row certificate verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
