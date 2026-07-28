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


def _is_integer(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def verify_witness(witness: object) -> list[str]:
    errors: list[str] = []
    if not isinstance(witness, dict):
        return ["witness must be an object"]

    for field in ("pattern", "window", "margin", "live_cells"):
        if field not in witness:
            errors.append(f"missing field: {field}")
    if errors:
        return errors

    pattern_data = witness["pattern"]
    pattern = None
    if not isinstance(pattern_data, dict):
        errors.append("pattern must be an object")
    else:
        name = pattern_data.get("name")
        rows = pattern_data.get("rows")
        if not isinstance(name, str):
            errors.append("pattern.name must be a string")
        if not isinstance(rows, list) or not all(isinstance(row, str) for row in rows):
            errors.append("pattern.rows must be an array of strings")
        if isinstance(name, str) and isinstance(rows, list) and all(
            isinstance(row, str) for row in rows
        ):
            try:
                pattern = PeriodicPattern(tuple(rows), name)
            except ValueError as error:
                errors.append(f"invalid pattern: {error}")

    window_data = witness["window"]
    window = None
    if not isinstance(window_data, dict):
        errors.append("window must be an object")
    else:
        window_values: dict[str, int] = {}
        for field in ("x", "y", "width", "height"):
            value = window_data.get(field)
            if not _is_integer(value):
                errors.append(f"window.{field} must be an integer")
            else:
                window_values[field] = value
        if len(window_values) == 4:
            try:
                window = Window(**window_values)
            except ValueError as error:
                errors.append(f"invalid window: {error}")

    margin_data = witness["margin"]
    margin = None
    if not _is_integer(margin_data):
        errors.append("margin must be a nonnegative integer")
    elif margin_data < 0:
        errors.append("margin must be a nonnegative integer")
    else:
        margin = margin_data

    cells_data = witness["live_cells"]
    live_cells: set[tuple[int, int]] | None = None
    if not isinstance(cells_data, list):
        errors.append("live_cells must be an array")
    else:
        parsed_cells: set[tuple[int, int]] = set()
        for index, cell in enumerate(cells_data):
            if not isinstance(cell, (list, tuple)) or len(cell) != 2:
                errors.append(f"live_cells[{index}] must be a coordinate pair")
                continue
            if not _is_integer(cell[0]) or not _is_integer(cell[1]):
                errors.append(f"live_cells[{index}] coordinates must be integers")
                continue
            parsed_cells.add((cell[0], cell[1]))
        live_cells = parsed_cells

    if errors:
        return errors
    assert pattern is not None and window is not None and margin is not None
    assert live_cells is not None
    return verify_cells(pattern, window, margin, live_cells)
