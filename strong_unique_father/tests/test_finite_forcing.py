from strong_unique_father.forcing import analyze_stabilization
from strong_unique_father.life import verify_image
from strong_unique_father.patterns import (
    KYNNOES_TILE,
    STABILIZATION_334,
    STABILIZATION_710,
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
