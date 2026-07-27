#!/usr/bin/env python3
"""Independently decode and check the 45-cell Garden-of-Eden target."""

import json
import re
import sys
from pathlib import Path

EXPECTED_RLE = (
    "3b2o3bo$2bo2bobobo$bobo2bo3bo$obobo2bobo$o2bobo2bo$bo2b3o2bo$"
    "2bo2bobo2bo$bobo2bobobo$o3bo2bobo$bobobo2bo$2bo3b2o!"
)


def decode(rle):
    rows = []
    for encoded in rle.removesuffix("!").split("$"):
        row = ""
        for count, state in re.findall(r"(\d*)([bo])", encoded):
            row += ("." if state == "b" else "O") * int(count or 1)
        rows.append(row.ljust(11, "."))
    return rows


def main(path):
    target = json.loads(Path(path).read_text(encoding="utf-8"))
    assert target["rule"] == "B3/S23"
    assert target["width"] == target["height"] == 11
    assert target["rle"] == EXPECTED_RLE
    assert target["rows"] == decode(EXPECTED_RLE)
    assert sum(row.count("O") for row in target["rows"]) == target["population"] == 45
    assert all(len(row) == 11 and set(row) <= {".", "O"} for row in target["rows"])
    print("GoE target OK: 11x11, population 45")


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    main(sys.argv[1] if len(sys.argv) == 2 else root / "artifacts/goe45-target.json")
