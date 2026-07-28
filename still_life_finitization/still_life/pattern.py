from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PeriodicPattern:
    rows: tuple[str, ...]
    name: str = "pattern"

    def __post_init__(self) -> None:
        if not self.rows or not self.rows[0]:
            raise ValueError("a tile must be nonempty")
        if any(len(row) != len(self.rows[0]) for row in self.rows):
            raise ValueError("tile rows must have equal length")
        if any(cell not in ".1" for row in self.rows for cell in row):
            raise ValueError("tile cells must be '.' or '1'")

    @property
    def width(self) -> int:
        return len(self.rows[0])

    @property
    def height(self) -> int:
        return len(self.rows)

    def alive(self, x: int, y: int) -> bool:
        return self.rows[y % self.height][x % self.width] == "1"

    def validate_still_life(self) -> list[str]:
        errors = []
        for y in range(self.height):
            for x in range(self.width):
                neighbors = sum(
                    self.alive(x + dx, y + dy)
                    for dy in (-1, 0, 1)
                    for dx in (-1, 0, 1)
                    if (dx, dy) != (0, 0)
                )
                alive = self.alive(x, y)
                if alive and neighbors not in (2, 3):
                    errors.append(f"live ({x},{y}) has {neighbors} neighbors")
                elif not alive and neighbors == 3:
                    errors.append(f"dead ({x},{y}) would be born")
        return errors

    def to_dict(self) -> dict[str, object]:
        return {"name": self.name, "rows": list(self.rows)}

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "PeriodicPattern":
        return cls(tuple(str(row) for row in data["rows"]), str(data["name"]))


@dataclass(frozen=True)
class Window:
    x: int
    y: int
    width: int
    height: int

    def __post_init__(self) -> None:
        if self.width <= 0 or self.height <= 0:
            raise ValueError("window dimensions must be positive")

    def cells(self):
        for y in range(self.y, self.y + self.height):
            for x in range(self.x, self.x + self.width):
                yield x, y

    def expand(self, margin: int) -> tuple[int, int, int, int]:
        if margin < 0:
            raise ValueError("margin must be nonnegative")
        return (
            self.x - margin,
            self.y - margin,
            self.x + self.width - 1 + margin,
            self.y + self.height - 1 + margin,
        )

    def to_dict(self) -> dict[str, int]:
        return {
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "Window":
        return cls(*(int(data[key]) for key in ("x", "y", "width", "height")))
