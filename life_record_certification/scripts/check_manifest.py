#!/usr/bin/env python3
"""Check every byte count and SHA-256 recorded in the artifact manifest."""

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main(path):
    manifest = json.loads(Path(path).read_text(encoding="utf-8"))
    assert manifest["schema"] == 1
    expected = set(manifest["files"])
    actual = {
        str(item.relative_to(ROOT))
        for item in (ROOT / "artifacts").rglob("*")
        if item.is_file() and item.name != "manifest.json"
    }
    assert actual == expected, (actual - expected, expected - actual)
    for name, metadata in manifest["files"].items():
        content = (ROOT / name).read_bytes()
        assert len(content) == metadata["bytes"], name
        assert hashlib.sha256(content).hexdigest() == metadata["sha256"], name
    print(f"manifest OK: {len(expected)} artifacts")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) == 2 else ROOT / "artifacts/manifest.json")
