from __future__ import annotations

from .pattern import PeriodicPattern, Window


def verify_cells(
    pattern: PeriodicPattern,
    window: Window,
    margin: int,
    live_cells: set[tuple[int, int]],
) -> list[str]:
    """Verify a witness directly, without using the SAT encoding."""
    errors: list[str] = []
    bounds = window.expand(margin)
    xmin, ymin, xmax, ymax = bounds

    outside = [
        cell
        for cell in live_cells
        if not (xmin <= cell[0] <= xmax and ymin <= cell[1] <= ymax)
    ]
    if outside:
        errors.append(f"{len(outside)} live cells lie outside the finite box")

    for x, y in window.cells():
        if ((x, y) in live_cells) != pattern.alive(x, y):
            errors.append(f"core mismatch at ({x},{y})")

    def alive(x: int, y: int) -> bool:
        return (x, y) in live_cells

    for y in range(ymin - 1, ymax + 2):
        for x in range(xmin - 1, xmax + 2):
            neighbors = sum(
                alive(x + dx, y + dy)
                for dy in (-1, 0, 1)
                for dx in (-1, 0, 1)
                if (dx, dy) != (0, 0)
            )
            if alive(x, y) and neighbors not in (2, 3):
                errors.append(f"live ({x},{y}) has {neighbors} neighbors")
            elif not alive(x, y) and neighbors == 3:
                errors.append(f"dead ({x},{y}) would be born")
    return errors


def verify_witness(witness: dict[str, object]) -> list[str]:
    pattern = PeriodicPattern.from_dict(witness["pattern"])
    window = Window.from_dict(witness["window"])
    margin = int(witness["margin"])
    live_cells = {tuple(map(int, cell)) for cell in witness["live_cells"]}
    return verify_cells(pattern, window, margin, live_cells)
