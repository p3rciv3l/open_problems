from __future__ import annotations

from dataclasses import dataclass

Cell = tuple[int, int]


@dataclass(frozen=True)
class Pattern:
    width: int
    height: int
    live: frozenset[Cell]

    @property
    def assignment(self) -> dict[Cell, bool]:
        return {
            (x, y): (x, y) in self.live
            for y in range(self.height)
            for x in range(self.width)
        }


KYNNOES_TILE = (
    "..##.#",
    "..#.##",
    "##....",
    ".#.##.",
    "#..##.",
    "##....",
)

STABILIZATION_334_RLE = """x = 32, y = 26, rule = B3/S23
8b2obo2b2obo2b2obo$8bob2o2bob2o2bob2o3b2o$6b2o4b2o4b2o4b2o2bo$b2obo2b
ob2o2bob2o2bob2o2bobo$bob2obo2b2obo2b2obo2b2obo2b2o$6b2o4b2o4b2o4b2o$
2b2obo2b2obo2b2obo2b2obo2b2obo$2bob2o2bob2o2bob2o2bob2o2bob2o$2o4b2o4b
2o4b2o4b2o4b2o$bob2o2bob2o2bob2o2bob2o2bob2o2bo$o2b2obo2b2obo2b2obo2b
2obo2b2obo$2o4b2o4b2o4b2o4b2o4b2o$2b2obo2b2obo2b2obo2b2obo2b2obo$2bob
2o2bob2o2bob2o2bob2o2bob2o$2o4b2o4b2o4b2o4b2o4b2o$bob2o2bob2o2bob2o2b
ob2o2bob2o2bo$o2b2obo2b2obo2b2obo2b2obo2b2obo$2o4b2o4b2o4b2o4b2o4b2o$
2b2obo2b2obo2b2obo2b2obo2b2obo$2bob2o2bob2o2bob2o2bob2o2bob2o$6b2o4b2o
4b2o4b2o$3b2o2bob2o2bob2o2bob2o2bob2obo$4bobo2b2obo2b2obo2b2obo2bob2o
$3bo2b2o4b2o4b2o4b2o$3b2o3b2obo2b2obo2b2obo$8bob2o2bob2o2bob2o!"""


def parse_rle(rle: str) -> Pattern:
    lines = [
        line.strip()
        for line in rle.splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    if not lines:
        raise ValueError("RLE has no header")
    header = lines[0]
    fields = {
        part.split("=")[0].strip(): part.split("=")[1].strip()
        for part in header.split(",")
        if "=" in part
    }
    width, height = int(fields["x"]), int(fields["y"])
    body = "".join(lines[1:]).split("!", 1)[0]
    live: set[Cell] = set()
    x = y = run = 0
    for char in body:
        if char.isdigit():
            run = 10 * run + int(char)
            continue
        count = run or 1
        run = 0
        if char in "oA":
            live.update((x + dx, y) for dx in range(count))
            x += count
        elif char in "b.":
            x += count
        elif char == "$":
            y += count
            x = 0
        else:
            raise ValueError(f"unsupported RLE token {char!r}")
    if any(x >= width or y >= height for x, y in live):
        raise ValueError("RLE exceeds declared dimensions")
    return Pattern(width, height, frozenset(live))


STABILIZATION_334 = parse_rle(STABILIZATION_334_RLE)


def expand_kynnoes_stabilization(
    pattern: Pattern, horizontal_repeats: int, vertical_repeats: int
) -> Pattern:
    if horizontal_repeats < 0 or vertical_repeats < 0:
        raise ValueError("repeat counts must be nonnegative")
    rows = [
        [(x, y) in pattern.live for x in range(pattern.width)]
        for y in range(pattern.height)
    ]
    for _ in range(horizontal_repeats):
        rows = [row[:12] + row[12:18] + row[12:] for row in rows]
    for _ in range(vertical_repeats):
        rows = rows[:10] + rows[10:16] + rows[10:]
    live = frozenset(
        (x, y)
        for y, row in enumerate(rows)
        for x, value in enumerate(row)
        if value
    )
    return Pattern(len(rows[0]), len(rows), live)


STABILIZATION_710 = expand_kynnoes_stabilization(STABILIZATION_334, 2, 2)
