"""Machine-checked form of Jason Summers' 2×n block-array extension.

The source RLE is the reaction published at
https://conwaylife.com/wiki/Block_array .  It contains a 2×4 block array,
one beehive, four loaves, and eight gliders, and settles to a 2×5 array at
generation 68.
"""
from dataclasses import dataclass

from .life import Pattern, trajectory
from .model import Box, LocalMove, TimedGlider, verify_move

_EXTENSION_RLE = (
    "bo$2bo$3o2$28bo$28bobo$6bobo19b2o$7b2o$7bo5$38bo$18bo5bo11b2o$"
    "17bobo3bobo11b2o$17bo2bobo2bo$18b2o3b2o3$7b2ob2ob2ob2o$"
    "7b2ob2ob2ob2o3b2o$20bo2bo$7b2ob2ob2ob2o3b2o$7b2ob2ob2ob2o3$"
    "18b2o3b2o8b3o$17bo2bobo2bo7bo$17bobo3bobo8bo$18bo5bo6$7bo$"
    "7b2o$6bobo19b2o$28bobo$28bo2$3o$2bo$bo!"
)


def parse_rle(body: str) -> Pattern:
    x = y = 0
    count = ""
    cells: set[tuple[int, int]] = set()
    for token in body:
        if token.isdigit():
            count += token
            continue
        run_length = int(count or 1)
        count = ""
        if token == "b":
            x += run_length
        elif token == "o":
            cells.update((x + offset, y) for offset in range(run_length))
            x += run_length
        elif token == "$":
            x = 0
            y += run_length
        elif token == "!":
            break
        elif not token.isspace():
            raise ValueError(f"invalid RLE token: {token!r}")
    return frozenset(cells)


def _components(cells: Pattern) -> tuple[Pattern, ...]:
    remaining = set(cells)
    components = []
    while remaining:
        seed = remaining.pop()
        component = {seed}
        frontier = [seed]
        while frontier:
            x, y = frontier.pop()
            neighbours = {
                cell for cell in remaining
                if max(abs(cell[0] - x), abs(cell[1] - y)) <= 1
            }
            remaining.difference_update(neighbours)
            component.update(neighbours)
            frontier.extend(neighbours)
        components.append(frozenset(component))
    return tuple(components)


def _block_array(width: int, left: int | None = None) -> Pattern:
    if left is None:
        left = 7 - 3 * (width - 4)
    return frozenset(
        (left + 3 * column + dx, 20 + 3 * row + dy)
        for column in range(width)
        for row in range(2)
        for dx in (0, 1)
        for dy in (0, 1)
    )

_INITIAL = parse_rle(_EXTENSION_RLE)
_GLIDERS = tuple(
    TimedGlider(0, component)
    for component in sorted(
        _components(_INITIAL),
        key=lambda cells: (min(y for _, y in cells), min(x for x, _ in cells)),
    )
    if len(component) == 5
)
_BASE_ARRAY = _block_array(4)
_CATALYSTS = _INITIAL - _BASE_ARRAY - frozenset().union(
    *(glider.cells for glider in _GLIDERS)
)


def two_row_extension(width: int) -> LocalMove:
    """Return the published reaction with an arbitrary left prefix (width ≥ 4)."""
    if width < 4:
        raise ValueError("the extension component requires at least four columns")
    left = 7 - 3 * (width - 4)
    initial_context = _block_array(width, left) | _CATALYSTS
    initial = initial_context | frozenset().union(*(g.cells for g in _GLIDERS))
    states = trajectory(initial, 68)
    activity = frozenset().union(*states)
    move = LocalMove(
        name=f"published_2x{width}_to_2x{width + 1}",
        duration=68,
        input_context=initial_context,
        input_gliders=_GLIDERS,
        output_context=_block_array(width + 1, left),
        output_gliders=(),
        affected_box=Box(
            min(x for x, _ in activity), min(y for _, y in activity),
            max(x for x, _ in activity), max(y for _, y in activity),
        ),
    )
    result = verify_move(move)
    if not result.valid:
        raise AssertionError(f"published extension failed: {result.errors}")
    return move


@dataclass(frozen=True)
class TwoRowExtensionTheorem:
    """Finite checks plus a radius-one domain-of-dependence certificate."""

    directly_verified_widths: tuple[int, ...]
    duration: int
    locality_cutoff_width: int
    locality_margin: int


def certify_two_row_extension_theorem() -> TwoRowExtensionTheorem:
    """Certify the 2×n→2×(n+1) reaction for every n ≥ 4.

    Widths 4 through 29 are simulated. For larger widths, the only new cells
    lie farther left. The nearest omitted live cell at width 29 is 70 cells from
    the leftmost catalyst/glider cell, exceeding Life's 68-cell causal radius
    by two. Hence all larger inputs agree on the complete generation-68
    domain of dependence of the finite perturbation. Outside that cone the
    2×n block array is a still life, proving the result for every larger n.
    """
    widths = tuple(range(4, 30))
    for width in widths:
        two_row_extension(width)
    perturbation = _CATALYSTS | frozenset().union(*(g.cells for g in _GLIDERS))
    leftmost_perturbation = min(x for x, _ in perturbation)
    nearest_omitted_block_right_edge = 7 - 3 * (29 - 4) - 3 + 1
    margin = leftmost_perturbation - nearest_omitted_block_right_edge - 68
    if margin <= 0:
        raise AssertionError("locality cutoff has no causal-cone margin")
    return TwoRowExtensionTheorem(widths, 68, 29, margin)
