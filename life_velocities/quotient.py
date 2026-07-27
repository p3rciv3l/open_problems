from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class StripQuotient:
    """A finite quotient of (time, longitudinal position, transverse position).

    The two longitudinal relations are

        (t + period, x + displacement, y) == (t, x, y)
        (t - seam_phase, x + length, y) == (t, x, y).

    The first is translation by ``displacement`` after ``period`` generations.
    The second joins the ends of the finite strip with an explicit temporal
    phase.  ``y`` is periodic with circumference ``width``.
    """

    period: int
    displacement: int
    length: int
    width: int
    seam_phase: int = 0

    def __post_init__(self) -> None:
        if self.period <= 0 or self.length <= 0 or self.width <= 0:
            raise ValueError("period, length, and width must be positive")
        if self.index <= 0:
            raise ValueError("quotient relations must have positive determinant")

    @property
    def index(self) -> int:
        return self.period * self.length + self.displacement * self.seam_phase

    @property
    def cell_count(self) -> int:
        return self.index * self.width

    def key(self, t: int, x: int, y: int) -> tuple[int, int, int]:
        """Return an exact coset key for a point of Z^2 x Z/width."""
        determinant = self.index
        return (
            (self.length * t + self.seam_phase * x) % determinant,
            (-self.displacement * t + self.period * x) % determinant,
            y % self.width,
        )

    def representatives(self) -> dict[tuple[int, int, int], tuple[int, int, int]]:
        """Enumerate one lattice representative for every quotient cell."""
        start = (0, 0, 0)
        todo = [start]
        result: dict[tuple[int, int, int], tuple[int, int, int]] = {}
        while todo:
            point = todo.pop()
            key = self.key(*point)
            if key in result:
                continue
            result[key] = point
            t, x, y = point
            todo.extend(
                (
                    (t + 1, x, y),
                    (t - 1, x, y),
                    (t, x + 1, y),
                    (t, x - 1, y),
                    (t, x, y + 1),
                    (t, x, y - 1),
                )
            )
        if len(result) != self.cell_count:
            raise AssertionError(
                f"enumerated {len(result)} cells, expected {self.cell_count}"
            )
        return result
