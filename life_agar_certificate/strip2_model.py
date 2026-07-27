"""Two-center, two-time-slice local model for Conway Life."""


WIDTH = 4
HEIGHT = 3
PATTERN_COUNT = 1 << (WIDTH * HEIGHT)


def bit(mask: int, x: int, y: int) -> int:
    return (mask >> (x + WIDTH * y)) & 1


def encode(values) -> int:
    return sum(value << index for index, value in enumerate(values))


def life_output(mask: int, x: int, y: int) -> int:
    center = bit(mask, x, y)
    neighbors = sum(
        bit(mask, x + dx, y + dy)
        for dy in (-1, 0, 1)
        for dx in (-1, 0, 1)
        if dx or dy
    )
    return int(neighbors == 3 or (center == 1 and neighbors == 2))


def tile_data(mask: int) -> tuple[int, int, int, int, int, int, int, int]:
    """Return center sum/codes and the translated spacetime face codes."""
    centers = [bit(mask, x, 1) for x in (1, 2)]
    outputs = [life_output(mask, x, 1) for x in (1, 2)]
    left = encode(
        [bit(mask, x, y) for y in range(3) for x in range(3)] + [outputs[0]]
    )
    right = encode(
        [bit(mask, x, y) for y in range(3) for x in range(1, 4)]
        + [outputs[1]]
    )
    top = encode(bit(mask, x, y) for y in range(2) for x in range(4))
    bottom = encode(bit(mask, x, y) for y in range(1, 3) for x in range(4))
    return (
        sum(centers),
        encode(centers),
        encode(outputs),
        left,
        right,
        top,
        bottom,
        sum(outputs),
    )
