from __future__ import annotations

import hashlib
import json
from pathlib import Path

from ..still_life.stripe_transfer import seed_specs, solve_seed


def main() -> None:
    seeds = []
    for index, (window, horizontal, vertical) in enumerate(seed_specs(), start=1):
        print(f"seed {index}/264: phase={window.y} {window.width}x{window.height}")
        seed, encoding = solve_seed(window, horizontal, vertical)
        seeds.append(seed.to_dict(encoding))
    payload = json.dumps(seeds, sort_keys=True, separators=(",", ":"))
    certificate = {
        "format": "alternating-row-pump-certificate-v1",
        "theorem": "all finite rectangular windows have stabilization margin at most 3",
        "pattern": {"name": "alternating-live-rows", "rows": ["1", "."]},
        "seed_sha256": hashlib.sha256(payload.encode()).hexdigest(),
        "summary": {
            "seed_count": 264,
            "finite_seed_count": 128,
            "horizontal_seed_count": 48,
            "vertical_seed_count": 64,
            "two_dimensional_seed_count": 24,
            "margin_bound": 3,
            "horizontal_pump_length": 3,
            "vertical_pump_length": 4,
        },
        "seeds": seeds,
    }
    Path(__file__).with_name("alternating_rows_certificate.json").write_text(
        json.dumps(certificate, indent=2, sort_keys=True) + "\n"
    )


if __name__ == "__main__":
    main()
