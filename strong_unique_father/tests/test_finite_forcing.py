from strong_unique_father.forcing import analyze_stabilization
from strong_unique_father.life import verify_image
from strong_unique_father.patterns import KYNNOES_TILE, STABILIZATION_334


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
