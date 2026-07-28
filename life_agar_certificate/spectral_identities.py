"""Exact algebra checks for Boolean and spectral Life identities."""

from collections import defaultdict
from fractions import Fraction

from temporal_charging_obstruction import step


OFFSETS = tuple(
    (dx, dy)
    for dy in (-1, 0, 1)
    for dx in (-1, 0, 1)
    if dx or dy
)


def multiply(left, right):
    result = [Fraction(0)] * (len(left) + len(right) - 1)
    for i, a in enumerate(left):
        for j, b in enumerate(right):
            result[i + j] += a * b
    return result


def delta_polynomial(k):
    polynomial = [Fraction(1)]
    denominator = 1
    for j in range(9):
        if j == k:
            continue
        polynomial = multiply(polynomial, [-j, 1])
        denominator *= k - j
    return [coefficient / denominator for coefficient in polynomial]


def evaluate(polynomial, value):
    result = Fraction(0)
    for coefficient in reversed(polynomial):
        result = result * value + coefficient
    return result


def life_indicators(center, neighbors):
    delta2 = evaluate(delta_polynomial(2), neighbors)
    delta3 = evaluate(delta_polynomial(3), neighbors)
    birth = (1 - center) * delta3
    survivor2 = center * delta2
    survivor3 = center * delta3
    survivor = survivor2 + survivor3
    death = center - survivor
    return birth, survivor2, survivor3, survivor, death


def neighbor_sums(state, width, height):
    result = []
    for y in range(height):
        for x in range(width):
            result.append(
                sum(
                    (state >> (((y + dy) % height) * width + (x + dx) % width))
                    & 1
                    for dx, dy in OFFSETS
                )
            )
    return result


def correlation(state, width, height, dx, dy):
    return sum(
        ((state >> (y * width + x)) & 1)
        * (
            (
                state
                >> (((y + dy) % height) * width + (x + dx) % width)
            )
            & 1
        )
        for y in range(height)
        for x in range(width)
    )


def verify_polynomial_rule():
    deltas = [delta_polynomial(k) for k in range(9)]
    for k, polynomial in enumerate(deltas):
        assert len(polynomial) == 9
        for neighbors in range(9):
            assert evaluate(polynomial, neighbors) == int(neighbors == k)

    for center in (0, 1):
        for neighbors in range(9):
            birth, survivor2, survivor3, survivor, death = life_indicators(
                center, neighbors
            )
            following = birth + survivor
            assert following == int(
                neighbors == 3 or (center and neighbors == 2)
            )
            assert birth * center == 0
            assert survivor * (1 - center) == 0
            assert birth * (neighbors - 3) == 0
            assert survivor * (neighbors - 2) * (neighbors - 3) == 0
            assert center == survivor + death
            assert following == birth + survivor2 + survivor3
    return deltas


def verify_symbol_identity():
    factored_kernel = defaultdict(int)
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            factored_kernel[dx, dy] += 1
    factored_kernel[0, 0] -= 1
    assert {key: value for key, value in factored_kernel.items() if value} == {
        offset: 1 for offset in OFFSETS
    }

    lambda_plus_four = {(0, 0): 4, (1, 0): -4, (0, 1): -4, (1, 1): 16}
    sos_expansion = defaultdict(int)
    sos_expansion[1, 1] += 12
    for exponent, coefficient in {
        (0, 0): 1,
        (1, 0): -1,
        (0, 1): -1,
        (1, 1): 1,
    }.items():
        sos_expansion[exponent] += 4 * coefficient
    assert dict(sos_expansion) == lambda_plus_four


def verify_parseval_identity(state, width, height):
    size = width * height
    counts = neighbor_sums(state, width, height)
    live = state.bit_count()
    adjacency = sum(
        ((state >> i) & 1) * counts[i] for i in range(size)
    )
    assert adjacency == sum(
        correlation(state, width, height, dx, dy) for dx, dy in OFFSETS
    )

    kernel_square = defaultdict(int)
    for dx1, dy1 in OFFSETS:
        for dx2, dy2 in OFFSETS:
            kernel_square[dx2 - dx1, dy2 - dy1] += 1
    neighbor_square = sum(count * count for count in counts)
    assert neighbor_square == sum(
        coefficient * correlation(state, width, height, dx, dy)
        for (dx, dy), coefficient in kernel_square.items()
    )

    density = Fraction(live, size)
    adjacency_mean = Fraction(adjacency, size)
    spectral_floor = 12 * density * density - 4 * density
    assert adjacency_mean >= spectral_floor
    return density, adjacency_mean, Fraction(neighbor_square, size)


def verify_degree_bounds():
    width, height = 4, 3
    size = width * height
    checked = 0
    maximum_density = Fraction(0)
    for state in range(1 << size):
        counts = neighbor_sums(state, width, height)
        if any(
            ((state >> i) & 1) and counts[i] > 3 for i in range(size)
        ):
            continue
        density, adjacency, _ = verify_parseval_identity(state, width, height)
        assert adjacency <= 3 * density
        assert adjacency >= 16 * density - 8
        assert density <= Fraction(8, 13)
        assert density <= Fraction(7, 12)
        maximum_density = max(maximum_density, density)
        checked += 1

    assert maximum_density == Fraction(1, 2)
    stripes = sum(
        1 << (y * 4 + x) for y in range(4) for x in range(4) if x % 2 == 0
    )
    density, adjacency, _ = verify_parseval_identity(stripes, 4, 4)
    assert density == Fraction(1, 2)
    assert adjacency == 1
    assert adjacency == 12 * density * density - 4 * density
    return checked, maximum_density


def verify_temporal_averages():
    width = height = 3
    following = [step(state, width, height) for state in range(1 << 9)]
    visited = set()
    cycles = 0
    for initial in range(1 << 9):
        path = []
        positions = {}
        state = initial
        while state not in positions and state not in visited:
            positions[state] = len(path)
            path.append(state)
            state = following[state]
        visited.update(path)
        if state not in positions:
            continue
        cycle = path[positions[state] :]
        births = deaths = 0
        for current in cycle:
            next_state = following[current]
            births += (next_state & ~current).bit_count()
            deaths += (current & ~next_state).bit_count()
        assert births == deaths
        cycles += 1
    return cycles


def verify_all():
    deltas = verify_polynomial_rule()
    verify_symbol_identity()
    checked, maximum_density = verify_degree_bounds()
    cycles = verify_temporal_averages()
    return {
        "delta2_coefficients": [str(value) for value in deltas[2]],
        "delta3_coefficients": [str(value) for value in deltas[3]],
        "degree_constrained_4x3_states": checked,
        "maximum_degree_constrained_4x3_density": str(maximum_density),
        "3x3_cycles": cycles,
    }


def main():
    report = verify_all()
    print("delta_2 coefficients:", " ".join(report["delta2_coefficients"]))
    print("delta_3 coefficients:", " ".join(report["delta3_coefficients"]))
    print(
        "degree-constrained 4x3 states:",
        report["degree_constrained_4x3_states"],
    )
    print("3x3 temporal cycles:", report["3x3_cycles"])
    print("all exact polynomial and spectral identity checks passed")


if __name__ == "__main__":
    main()
