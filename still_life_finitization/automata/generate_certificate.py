from __future__ import annotations

import json
from pathlib import Path

from ..still_life.transfer import analyze_component_agar, block_agar


def main() -> None:
    certificate = analyze_component_agar(block_agar())
    output = Path(__file__).with_name("block_4x4_certificate.json")
    output.write_text(json.dumps(certificate, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
