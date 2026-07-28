"""Independent explicit-state verifier for macro-rule certificates."""

from .life import Pattern, evolve, translate
from .sat_macro_rule import MacroGeometry, outside_context_is_excluded


def verify_macro_tile(
    tile: Pattern,
    geometry: MacroGeometry,
    rule: int,
) -> bool:
    geometry.validate()
    if not tile:
        return False
    if (
        min(x for x, _ in tile) != 0
        or max(x for x, _ in tile) != geometry.width - 1
        or min(y for _, y in tile) != 0
        or max(y for _, y in tile) != geometry.height - 1
    ):
        return False
    if not outside_context_is_excluded(geometry):
        return False

    window_left = -((geometry.pitch - geometry.width) // 2)
    window = {
        (x, y)
        for y in range(-geometry.time, geometry.height + geometry.time)
        for x in range(window_left, window_left + geometry.pitch)
    }
    for context in range(8):
        initial = frozenset().union(
            *(
                translate(tile, (site * geometry.pitch, 0))
                for bit, site in ((4, -1), (2, 0), (1, 1))
                if context & bit
            )
        )
        actual = evolve(initial, geometry.time) & window
        expected = tile if (rule >> context) & 1 else frozenset()
        if actual != expected:
            return False
    return True


def exhaustive_tiles(geometry: MacroGeometry, rule: int) -> tuple[Pattern, ...]:
    witnesses = []
    for mask in range(1, 1 << (geometry.width * geometry.height)):
        tile = frozenset(
            (x, y)
            for y in range(geometry.height)
            for x in range(geometry.width)
            if (mask >> (y * geometry.width + x)) & 1
        )
        if verify_macro_tile(tile, geometry, rule):
            witnesses.append(tile)
    return tuple(witnesses)
