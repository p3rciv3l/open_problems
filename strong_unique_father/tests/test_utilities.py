import pytest

from strong_unique_father.life import convex_hull_cells
from strong_unique_father.patterns import Pattern, parse_rle


def test_parse_rle_accepts_leading_comment_metadata() -> None:
    pattern = parse_rle(
        """
        #N Commented glider
        #O Test Author
        #C Standard RLE metadata may precede the header.
        x = 3, y = 3, rule = B3/S23
        bo$2bo$3o!
        """
    )

    assert pattern == Pattern(
        width=3,
        height=3,
        live=frozenset({(1, 0), (2, 1), (0, 2), (1, 2), (2, 2)}),
    )


@pytest.mark.parametrize(
    ("endpoints", "expected"),
    [
        ({(1, 2), (4, 2)}, {(1, 2), (2, 2), (3, 2), (4, 2)}),
        ({(3, -1), (3, 2)}, {(3, -1), (3, 0), (3, 1), (3, 2)}),
        ({(-1, -1), (2, 2)}, {(-1, -1), (0, 0), (1, 1), (2, 2)}),
        ({(0, 0), (6, 4)}, {(0, 0), (3, 2), (6, 4)}),
    ],
    ids=["horizontal", "vertical", "diagonal", "non-axis-aligned"],
)
def test_two_point_hull_enumerates_lattice_segment(
    endpoints: set[tuple[int, int]], expected: set[tuple[int, int]]
) -> None:
    assert convex_hull_cells(frozenset(endpoints)) == expected
