"""Radius-one local model for Conway Life."""


def bit(mask: int, x: int, y: int) -> int:
    return (mask >> (x + 3 * y)) & 1


def encode(values) -> int:
    return sum(value << index for index, value in enumerate(values))


def life_output(mask: int) -> int:
    center = bit(mask, 1, 1)
    neighbors = mask.bit_count() - center
    return int(neighbors == 3 or (center == 1 and neighbors == 2))


def tile_data(mask: int) -> tuple[int, int, int, int, int, int]:
    """Return center, next, left, right, top, bottom face codes."""
    center = bit(mask, 1, 1)
    nxt = life_output(mask)
    left = encode(bit(mask, x, y) for y in range(3) for x in range(2))
    right = encode(bit(mask, x, y) for y in range(3) for x in range(1, 3))
    top = encode(bit(mask, x, y) for y in range(2) for x in range(3))
    bottom = encode(bit(mask, x, y) for y in range(1, 3) for x in range(3))
    return center, nxt, left, right, top, bottom
