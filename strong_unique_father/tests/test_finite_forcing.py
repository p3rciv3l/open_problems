from strong_unique_father.forcing import analyze_stabilization
from strong_unique_father.life import convex_hull_cells, evolve_finite, verify_image
from strong_unique_father.patterns import (
    KYNNOES_BOUNDARY_OBSTRUCTION,
    KYNNOES_TILE,
    STABILIZATION_334,
    STABILIZATION_710,
    expand_kynnoes_stabilization,
    kynnoes_boundary_counter_predecessor,
    kynnoes_family_combinatorics,
)


def test_published_pattern_is_still_life() -> None:
    image = STABILIZATION_334.assignment
    predecessor = {
        (x, y): (x, y) in STABILIZATION_334.live
        for y in range(-1, STABILIZATION_334.height + 1)
        for x in range(-1, STABILIZATION_334.width + 1)
    }
    assert len(STABILIZATION_334.live) == 334
    assert verify_image(predecessor, image)


def test_interior_is_kynnoes_agar_phase() -> None:
    image = STABILIZATION_334.assignment
    matches = []
    for dx in range(6):
        for dy in range(6):
            matches.append(
                all(
                    image[x, y] == (KYNNOES_TILE[(y + dy) % 6][(x + dx) % 6] == "#")
                    for y in range(6, 20)
                    for x in range(6, 26)
                )
            )
    assert any(matches)


def test_metrics_and_counter_predecessors() -> None:
    report = analyze_stabilization(STABILIZATION_334)
    assert report["population"] == 334
    assert report["live_cells"] == {
        "requested": 334,
        "forced": 286,
        "fraction": 286 / 334,
        "complete": False,
    }
    assert report["convex_hull_assignment"] == {
        "requested": 740,
        "forced": 662,
        "fraction": 662 / 740,
        "complete": False,
    }
    assert len(report["counter_predecessors"]) == 78
    image = STABILIZATION_334.assignment
    for key, serialized in report["counter_predecessors"].items():
        cell = tuple(map(int, key.split(",")))
        witness = {(x, y): bool(value) for x, y, value in serialized}
        assert witness[cell] != image[cell]
        assert verify_image(witness, image)


def test_expanded_stabilization_improves_coverage_with_dead_annulus() -> None:
    image = STABILIZATION_710.assignment
    predecessor = {
        (x, y): (x, y) in STABILIZATION_710.live
        for y in range(-1, STABILIZATION_710.height + 1)
        for x in range(-1, STABILIZATION_710.width + 1)
    }
    assert (STABILIZATION_710.width, STABILIZATION_710.height) == (44, 38)
    assert len(STABILIZATION_710.live) == 710
    assert verify_image(predecessor, image)

    report = analyze_stabilization(STABILIZATION_710, output_annulus=2)
    assert report["live_cells"] == {
        "requested": 710,
        "forced": 646,
        "fraction": 646 / 710,
        "complete": False,
    }
    assert report["convex_hull_assignment"] == {
        "requested": 1580,
        "forced": 1478,
        "fraction": 1478 / 1580,
        "complete": False,
    }
    assert len(report["counter_predecessors"]) == 102
    assert report["claim_scope"]["dead_output_annulus"] == 2
    assert report["claim_scope"]["strong_unique_father_solved"] is False


def test_parametric_family_combinatorics() -> None:
    for repeats in range(6):
        pattern = expand_kynnoes_stabilization(
            STABILIZATION_334, repeats, repeats
        )
        expected = kynnoes_family_combinatorics(repeats)
        assert pattern.width == expected["width"]
        assert pattern.height == expected["height"]
        assert len(pattern.live) == expected["population"]
        assert len(convex_hull_cells(pattern.live)) == expected["convex_hull_cells"]


def test_exact_boundary_obstruction_applies_to_entire_family() -> None:
    assert (8, 0) in STABILIZATION_334.live
    assert (8, 0) in KYNNOES_BOUNDARY_OBSTRUCTION
    for repeats in (0, 1, 2, 5, 10):
        pattern = expand_kynnoes_stabilization(
            STABILIZATION_334, repeats, repeats
        )
        predecessor = kynnoes_boundary_counter_predecessor(pattern)
        assert (8, 0) not in predecessor
        assert evolve_finite(predecessor) == pattern.live
