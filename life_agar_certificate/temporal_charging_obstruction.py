"""Exact finite checks for population-only temporal charging obstructions."""

from fractions import Fraction


def step(state, width, height):
    result = 0
    for y in range(height):
        for x in range(width):
            neighbors = 0
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    if dx or dy:
                        j = ((y + dy) % height) * width + (x + dx) % width
                        neighbors += (state >> j) & 1
            i = y * width + x
            live = (state >> i) & 1
            if neighbors == 3 or (live and neighbors == 2):
                result |= 1 << i
    return result


def transition_counts(state, width, height):
    following = step(state, width, height)
    survivors = state & following
    births = following & ~state
    deaths = state & ~following
    return tuple(x.bit_count() for x in (survivors, births, deaths))


def directed_edges(left, right, width, height):
    count = 0
    for y in range(height):
        for x in range(width):
            i = y * width + x
            if not (left >> i) & 1:
                continue
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    if dx or dy:
                        j = ((y + dy) % height) * width + (x + dx) % width
                        count += (right >> j) & 1
    return count


def verify_all_long_prefixes_3x3():
    width = height = 3
    size = width * height
    following = [step(state, width, height) for state in range(1 << size)]

    for initial in range(1 << size):
        state = initial
        centered_sum = 0
        seen = {}
        centered_prefixes = []
        while state not in seen:
            seen[state] = len(centered_prefixes)
            centered_sum += 2 * state.bit_count() - size
            centered_prefixes.append(centered_sum)
            state = following[state]

        cycle_start = seen[state]
        cycle_weight = centered_sum
        if cycle_start:
            cycle_weight -= centered_prefixes[cycle_start - 1]
        assert cycle_weight <= 0

        end = len(centered_prefixes)
        if cycle_weight < 0:
            end += len(centered_prefixes) - cycle_start
        for length in range(len(centered_prefixes) + 1, end + 1):
            centered_sum += 2 * state.bit_count() - size
            centered_prefixes.append(centered_sum)
            state = following[state]

        assert max(centered_prefixes[2:], default=0) <= 0


def verify_survivor_stability_obstruction():
    """Disprove the coefficient-one survivor-deficit stability inequality."""
    width = height = 3
    size = width * height
    maximum_ratio = Fraction()
    maximizers = []
    for state in range(1 << size):
        survivors, births, deaths = transition_counts(state, width, height)
        deficit = Fraction(size, 2) - survivors
        assert deficit >= 0
        if not deficit:
            assert births == 0
            continue
        ratio = Fraction(births, 1) / deficit
        if ratio > maximum_ratio:
            maximum_ratio = ratio
            maximizers = [(state, survivors, births, deaths)]
        elif ratio == maximum_ratio:
            maximizers.append((state, survivors, births, deaths))

    row = 0b000_000_111
    assert (row, 3, 6, 0) in maximizers
    assert maximum_ratio == 4
    return {
        "states": 1 << size,
        "maximum_birth_to_survivor_deficit_ratio": str(maximum_ratio),
        "maximizers": len(maximizers),
    }


def main():
    row = 0b000_000_111
    full = (1 << 9) - 1
    assert step(row, 3, 3) == full
    assert step(full, 3, 3) == 0
    assert transition_counts(row, 3, 3) == (3, 6, 0)
    assert transition_counts(full, 3, 3) == (0, 0, 9)

    survivors = row
    births = full ^ row
    assert directed_edges(births, survivors, 3, 3) == 18
    assert directed_edges(births, 0, 3, 3) == 0
    assert directed_edges(survivors, survivors, 3, 3) == 6
    assert 3 + 9 > 9

    stability = verify_survivor_stability_obstruction()
    verify_all_long_prefixes_3x3()

    transient = 0x557
    stripes = 0x555
    assert step(transient, 4, 3) == stripes
    assert step(stripes, 4, 3) == stripes
    assert transition_counts(transient, 4, 3) == (6, 0, 1)
    assert directed_edges(stripes, stripes, 4, 3) == 12
    for length in range(3, 100):
        assert 7 + 6 * (length - 1) > 6 * length

    print("3x3 row -> full -> empty counts: 3, 9, 0")
    print(
        "3x3 exhaustive maximum birth/survivor-deficit ratio: "
        f"{stability['maximum_birth_to_survivor_deficit_ratio']}"
    )
    print("3x3 exhaustive check: every prefix of length >= 3 has average <= 1/2")
    print("4x3 transient -> stripes -> stripes counts: 7, 6, 6, ...")
    print("all temporal-charging obstruction checks passed")


if __name__ == "__main__":
    main()
