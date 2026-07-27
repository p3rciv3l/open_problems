import csv
import json
from pathlib import Path

from life_safety import check_all_single_gliders, check_bounded_flip

HERE = Path(__file__).parent
EXAMPLES = HERE / "examples"


def main() -> None:
    safe_target = frozenset({(-1, 0), (0, 0), (1, 0)})
    safe = check_bounded_flip(safe_target, (-1, 1, -1, 1), (0, 0), 1)

    block = frozenset({(0, 0), (1, 0), (0, 1), (1, 1)})
    unsafe = check_bounded_flip(block, (0, 1, 0, 1), (0, 0), 1)
    results = check_all_single_gliders(block, collision_horizon=128)

    with (EXAMPLES / "bounded_results.json").open("w") as output:
        json.dump(
            {
                "one_tick_safe": safe.as_dict(),
                "block_counterexample": unsafe.as_dict(),
            },
            output,
            indent=2,
        )
        output.write("\n")

    with (EXAMPLES / "block_single_gliders.csv").open("w", newline="") as output:
        writer = csv.writer(output)
        writer.writerow(
            [
                "direction",
                "phase",
                "lane",
                "outcome",
                "restored_generation",
                "settled_generation",
                "settled_period",
                "population_at_stop",
            ]
        )
        for result in results:
            writer.writerow(
                [
                    result.attack.direction,
                    result.attack.phase,
                    result.attack.lane,
                    result.outcome,
                    result.restored_generation,
                    result.settled_generation,
                    result.settled_period,
                    len(result.final),
                ]
            )

    counterexample = next(
        result for result in results if result.outcome == "changed_periodic"
    )
    with (EXAMPLES / "block_collision_counterexample.json").open("w") as output:
        json.dump(counterexample.as_dict(), output, indent=2)
        output.write("\n")


if __name__ == "__main__":
    main()
