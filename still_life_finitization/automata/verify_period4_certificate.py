from __future__ import annotations

import json
from pathlib import Path

from ..still_life.period4_transfer import verify_period4_certificate


def main() -> None:
    path = Path(__file__).with_name("period4_certificate.json")
    errors = verify_period4_certificate(json.loads(path.read_text()))
    if errors:
        raise SystemExit("\n".join(errors))
    print("verified")


if __name__ == "__main__":
    main()
