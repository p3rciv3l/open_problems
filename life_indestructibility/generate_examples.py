import csv
import json
from pathlib import Path

from life_safety import (
    check_all_single_gliders,
    check_bounded_flip,
    exclude_still_life_classes,
    search_still_life_classes,
    search_three_by_three_invariant,
)
from life_safety.life import serialize

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

    center_alive = search_three_by_three_invariant(True)
    center_dead = search_three_by_three_invariant(False)
    with (EXAMPLES / "boundary_invariant_3x3_exclusion.json").open("w") as output:
        json.dump(
            {
                "both_center_values_excluded": (
                    center_alive.excluded and center_dead.excluded
                ),
                "center_alive": center_alive.as_dict(),
                "center_dead": center_dead.as_dict(),
            },
            output,
            indent=2,
        )
        output.write("\n")

    candidates = search_still_life_classes(collision_horizon=256)
    with (EXAMPLES / "still_life_4x4_candidates.csv").open(
        "w", newline=""
    ) as output:
        writer = csv.writer(output)
        writer.writerow(
            [
                "candidate",
                "population",
                "pattern",
                "attacks",
                "restored",
                "changed_periodic",
                "unresolved_by_horizon",
                "excluded_by_certified_collision",
                "witness_direction",
                "witness_phase",
                "witness_lane",
                "witness_settled_generation",
                "witness_period",
            ]
        )
        for result in candidates:
            witness = result.exclusion_witness
            writer.writerow(
                [
                    result.candidate.identifier,
                    len(result.candidate.pattern),
                    json.dumps(serialize(result.candidate.pattern), separators=(",", ":")),
                    len(result.collisions),
                    result.restored,
                    result.settled_changed,
                    result.unresolved,
                    witness is not None,
                    witness.attack.direction if witness else "",
                    witness.attack.phase if witness else "",
                    witness.attack.lane if witness else "",
                    witness.settled_generation if witness else "",
                    witness.settled_period if witness else "",
                ]
            )

    with (EXAMPLES / "still_life_4x4_attacks.csv").open(
        "w", newline=""
    ) as output:
        writer = csv.writer(output)
        writer.writerow(
            [
                "candidate",
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
        for result in candidates:
            for collision in result.collisions:
                writer.writerow(
                    [
                        result.candidate.identifier,
                        collision.attack.direction,
                        collision.attack.phase,
                        collision.attack.lane,
                        collision.outcome,
                        collision.restored_generation,
                        collision.settled_generation,
                        collision.settled_period,
                        len(collision.final),
                    ]
                )

    exclusions = exclude_still_life_classes()
    with (EXAMPLES / "still_life_5x5_exclusion.csv").open(
        "w", newline=""
    ) as output:
        writer = csv.writer(output, lineterminator="\n")
        writer.writerow(
            [
                "candidate",
                "population",
                "pattern",
                "attack_count",
                "attacks_tried",
                "excluded",
                "witness_direction",
                "witness_phase",
                "witness_lane",
                "witness_settled_generation",
                "witness_period",
            ]
        )
        for exclusion in exclusions:
            witness = exclusion.witness
            writer.writerow(
                [
                    exclusion.candidate.identifier,
                    len(exclusion.candidate.pattern),
                    json.dumps(
                        serialize(exclusion.candidate.pattern),
                        separators=(",", ":"),
                    ),
                    exclusion.attack_count,
                    exclusion.attacks_tried,
                    witness is not None,
                    witness.attack.direction if witness else "",
                    witness.attack.phase if witness else "",
                    witness.attack.lane if witness else "",
                    witness.settled_generation if witness else "",
                    witness.settled_period if witness else "",
                ]
            )


if __name__ == "__main__":
    main()
