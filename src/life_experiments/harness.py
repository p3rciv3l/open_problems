from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import platform
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable

import numpy as np

EMPIRICAL_LABEL = (
    "EMPIRICAL FINITE-SIZE RESULTS: finite periodic tori and finite run lengths; "
    "no asymptotic theorem is inferred."
)


@dataclass(frozen=True)
class ExperimentConfig:
    p: float
    size: int
    steps: int
    trials: int
    sample_every: int = 1
    master_seed: int = 0
    confidence: float = 0.95

    def validate(self) -> None:
        if not 0.0 <= self.p <= 1.0:
            raise ValueError("p must be in [0, 1]")
        if self.size < 1 or self.steps < 0 or self.trials < 1:
            raise ValueError("size and trials must be positive; steps must be nonnegative")
        if self.sample_every < 1:
            raise ValueError("sample_every must be positive")
        if not 0.0 < self.confidence < 1.0:
            raise ValueError("confidence must be in (0, 1)")


def step_numpy(states: np.ndarray) -> np.ndarray:
    """Advance one or more periodic square Life grids by one generation."""
    if states.ndim not in (2, 3) or states.shape[-1] != states.shape[-2]:
        raise ValueError("states must have shape (L, L) or (trials, L, L)")
    states = np.asarray(states, dtype=np.bool_)
    neighbors = np.zeros(states.shape, dtype=np.uint8)
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            if dy or dx:
                neighbors += np.roll(states, shift=(dy, dx), axis=(-2, -1))
    return (neighbors == 3) | (states & (neighbors == 2))


def step_scalar(state: np.ndarray) -> np.ndarray:
    """Simple scalar reference implementation for validation."""
    state = np.asarray(state, dtype=np.bool_)
    if state.ndim != 2 or state.shape[0] != state.shape[1]:
        raise ValueError("state must have shape (L, L)")
    size = state.shape[0]
    result = np.zeros_like(state)
    for y in range(size):
        for x in range(size):
            neighbors = 0
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    if dy or dx:
                        neighbors += int(state[(y + dy) % size, (x + dx) % size])
            result[y, x] = neighbors == 3 or (state[y, x] and neighbors == 2)
    return result


def trial_seed(master_seed: int, p: float, size: int, trial: int) -> int:
    payload = f"{master_seed}|{p.hex()}|{size}|{trial}".encode()
    return int.from_bytes(hashlib.blake2b(payload, digest_size=8).digest(), "little")


def _z_value(confidence: float) -> float:
    from statistics import NormalDist

    return NormalDist().inv_cdf(0.5 + confidence / 2.0)


def _summary(values: np.ndarray, confidence: float, bounded: bool = False) -> dict[str, Any]:
    values = np.asarray(values, dtype=np.float64)
    values = values[np.isfinite(values)]
    if values.size == 0:
        return {"mean": None, "ci_low": None, "ci_high": None, "n": 0}
    mean = float(values.mean())
    if values.size == 1:
        low = high = mean
    else:
        half_width = _z_value(confidence) * float(values.std(ddof=1)) / math.sqrt(values.size)
        low, high = mean - half_width, mean + half_width
    if bounded:
        low, high = max(0.0, low), min(1.0, high)
    return {"mean": mean, "ci_low": low, "ci_high": high, "n": int(values.size)}


def _initial_states(config: ExperimentConfig) -> tuple[np.ndarray, list[int]]:
    seeds = [trial_seed(config.master_seed, config.p, config.size, i) for i in range(config.trials)]
    states = np.empty((config.trials, config.size, config.size), dtype=np.bool_)
    for i, seed in enumerate(seeds):
        states[i] = np.random.default_rng(seed).random((config.size, config.size)) < config.p
    return states, seeds


def run_experiment(config: ExperimentConfig) -> dict[str, Any]:
    config.validate()
    started = time.perf_counter()
    states, seeds = _initial_states(config)
    seen: list[dict[bytes, int]] = [{states[i].tobytes(): 0} for i in range(config.trials)]
    detected_at: list[int | None] = [None] * config.trials
    transient: list[int | None] = [None] * config.trials
    periods: list[int | None] = [None] * config.trials
    measurements: list[dict[str, Any]] = []

    def record(generation: int, activity: np.ndarray | None) -> None:
        density = states.mean(axis=(-2, -1))
        row: dict[str, Any] = {
            "generation": generation,
            "density": _summary(density, config.confidence, bounded=True),
            "activity": _summary(activity, config.confidence, bounded=True)
            if activity is not None
            else {"mean": None, "ci_low": None, "ci_high": None, "n": 0},
        }
        measurements.append(row)

    record(0, None)
    for generation in range(1, config.steps + 1):
        previous = states
        states = step_numpy(states)
        activity = np.not_equal(states, previous).mean(axis=(-2, -1))

        for trial in range(config.trials):
            if periods[trial] is not None:
                continue
            key = states[trial].tobytes()
            first = seen[trial].get(key)
            if first is None:
                seen[trial][key] = generation
            else:
                transient[trial] = first
                periods[trial] = generation - first
                detected_at[trial] = generation
                seen[trial].clear()

        if generation % config.sample_every == 0 or generation == config.steps:
            record(generation, activity)

    detected_periods = np.array([p for p in periods if p is not None], dtype=np.float64)
    detected_transients = np.array([t for t in transient if t is not None], dtype=np.float64)
    detections = np.array([p is not None for p in periods], dtype=np.float64)
    return {
        "label": EMPIRICAL_LABEL,
        "config": asdict(config),
        "trial_seeds": seeds,
        "measurements": measurements,
        "period_detection": {
            "detected_fraction": _summary(detections, config.confidence, bounded=True),
            "period_detected_only": _summary(detected_periods, config.confidence),
            "transient_detected_only": _summary(detected_transients, config.confidence),
            "trials": [
                {
                    "trial": i,
                    "seed": seeds[i],
                    "detected": periods[i] is not None,
                    "transient": transient[i],
                    "period": periods[i],
                    "detected_at": detected_at[i],
                }
                for i in range(config.trials)
            ],
        },
        "elapsed_seconds": time.perf_counter() - started,
    }


def _csv_rows(result: dict[str, Any]) -> Iterable[dict[str, Any]]:
    config = result["config"]
    period = result["period_detection"]
    for measurement in result["measurements"]:
        yield {
            "result_scope": "empirical_finite_size",
            "p": config["p"],
            "L": config["size"],
            "steps": config["steps"],
            "trials": config["trials"],
            "master_seed": config["master_seed"],
            "confidence": config["confidence"],
            "generation": measurement["generation"],
            "density_mean": measurement["density"]["mean"],
            "density_ci_low": measurement["density"]["ci_low"],
            "density_ci_high": measurement["density"]["ci_high"],
            "activity_mean": measurement["activity"]["mean"],
            "activity_ci_low": measurement["activity"]["ci_low"],
            "activity_ci_high": measurement["activity"]["ci_high"],
            "period_detected_fraction": period["detected_fraction"]["mean"],
            "period_detected_ci_low": period["detected_fraction"]["ci_low"],
            "period_detected_ci_high": period["detected_fraction"]["ci_high"],
            "detected_period_mean": period["period_detected_only"]["mean"],
        }


def write_outputs(results: list[dict[str, Any]], output_prefix: Path) -> tuple[Path, Path]:
    output_prefix.parent.mkdir(parents=True, exist_ok=True)
    json_path = output_prefix.with_suffix(".json")
    csv_path = output_prefix.with_suffix(".csv")
    document = {
        "label": EMPIRICAL_LABEL,
        "schema_version": 1,
        "backend": "numpy",
        "environment": {"python": platform.python_version(), "numpy": np.__version__},
        "experiments": results,
    }
    json_path.write_text(json.dumps(document, indent=2, sort_keys=True) + "\n")
    rows = [row for result in results for row in _csv_rows(result)]
    fieldnames = list(rows[0]) if rows else []
    with csv_path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    return json_path, csv_path


def run_sweep(
    probabilities: Iterable[float],
    sizes: Iterable[int],
    steps: Iterable[int],
    trials: int,
    sample_every: int,
    master_seed: int,
    confidence: float,
) -> list[dict[str, Any]]:
    return [
        run_experiment(
            ExperimentConfig(
                p=p,
                size=size,
                steps=duration,
                trials=trials,
                sample_every=sample_every,
                master_seed=master_seed,
                confidence=confidence,
            )
        )
        for p in probabilities
        for size in sizes
        for duration in steps
    ]


def _comma_values(value: str, cast: Any) -> list[Any]:
    return [cast(item.strip()) for item in value.split(",") if item.strip()]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=EMPIRICAL_LABEL)
    parser.add_argument("--p", default="0.1,0.3,0.5,0.7", help="comma-separated probabilities")
    parser.add_argument("--sizes", default="32,64,128", help="comma-separated torus side lengths")
    parser.add_argument("--steps", default="200", help="comma-separated run lengths")
    parser.add_argument("--trials", type=int, default=12)
    parser.add_argument("--sample-every", type=int, default=10)
    parser.add_argument("--seed", type=int, default=20260727)
    parser.add_argument("--confidence", type=float, default=0.95)
    parser.add_argument("--output", type=Path, default=Path("results/life_sweep"))
    args = parser.parse_args(argv)

    results = run_sweep(
        _comma_values(args.p, float),
        _comma_values(args.sizes, int),
        _comma_values(args.steps, int),
        args.trials,
        args.sample_every,
        args.seed,
        args.confidence,
    )
    json_path, csv_path = write_outputs(results, args.output)
    print(EMPIRICAL_LABEL)
    print(f"Wrote {json_path} and {csv_path} ({len(results)} configurations)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
