import csv
import json

import numpy as np
import pytest

from life_experiments.harness import (
    EMPIRICAL_LABEL,
    ExperimentConfig,
    run_experiment,
    step_numpy,
    step_scalar,
    trial_seed,
    write_outputs,
)


@pytest.mark.parametrize("size", [1, 2, 3, 5, 8])
def test_numpy_matches_scalar_random_states(size):
    rng = np.random.default_rng(1234 + size)
    states = rng.random((7, size, size)) < 0.4
    actual = step_numpy(states)
    expected = np.stack([step_scalar(state) for state in states])
    np.testing.assert_array_equal(actual, expected)


def test_numpy_matches_scalar_over_multiple_generations():
    rng = np.random.default_rng(991)
    fast = rng.random((9, 9)) < 0.35
    slow = fast.copy()
    for _ in range(20):
        fast = step_numpy(fast)
        slow = step_scalar(slow)
        np.testing.assert_array_equal(fast, slow)


def test_fixed_point_period_and_measurements():
    config = ExperimentConfig(p=0.0, size=5, steps=4, trials=3, master_seed=7)
    result = run_experiment(config)
    assert result["period_detection"]["detected_fraction"]["mean"] == 1.0
    assert result["period_detection"]["period_detected_only"]["mean"] == 1.0
    assert result["measurements"][0]["density"]["mean"] == 0.0
    assert result["measurements"][1]["activity"]["mean"] == 0.0


def test_blinker_evolution_has_period_two():
    vertical = np.zeros((5, 5), dtype=np.bool_)
    vertical[1:4, 2] = True
    horizontal = np.zeros((5, 5), dtype=np.bool_)
    horizontal[2, 1:4] = True

    generation_one = step_numpy(vertical)
    generation_two = step_numpy(generation_one)

    np.testing.assert_array_equal(generation_one, horizontal)
    np.testing.assert_array_equal(generation_two, vertical)
    assert not np.array_equal(generation_one, vertical)


def test_seed_and_results_are_deterministic():
    config = ExperimentConfig(p=0.37, size=10, steps=12, trials=4, master_seed=42)
    first = run_experiment(config)
    second = run_experiment(config)
    assert first["trial_seeds"] == second["trial_seeds"]
    assert first["measurements"] == second["measurements"]
    assert first["period_detection"] == second["period_detection"]
    assert trial_seed(42, 0.37, 10, 0) != trial_seed(42, 0.37, 10, 1)


def test_output_formats_and_labels(tmp_path):
    result = run_experiment(
        ExperimentConfig(p=0.25, size=6, steps=3, trials=2, sample_every=2)
    )
    json_path, csv_path = write_outputs([result], tmp_path / "sweep")

    document = json.loads(json_path.read_text())
    assert document["label"] == EMPIRICAL_LABEL
    assert document["experiments"][0]["label"] == EMPIRICAL_LABEL
    with csv_path.open(newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert rows
    assert {row["result_scope"] for row in rows} == {"empirical_finite_size"}
    assert [int(row["generation"]) for row in rows] == [0, 2, 3]
