"""Print reproducible bounded findings for the built-in corpus."""
from .analysis import bounded_closure
from .block_arrays import BlockArrayInstance, assess
from .reactions import BUILTIN_REACTIONS, verify_builtins


def main() -> None:
    verifications = verify_builtins()
    for result in verifications:
        status = "PASS" if result.valid else "FAIL"
        print(
            f"{status} {result.move_name}: stable={result.first_stable_generation} "
            f"activity_box={result.activity_box}"
        )
        for error in result.errors:
            print(f"  {error}")

    closure = bounded_closure(BUILTIN_REACTIONS, max_steps=3)
    print(f"reachable canonical contexts from empty: {len(closure.reached)}")
    for state, witness in sorted(closure.witnesses.items()):
        print(f"  cells={len(state)} witness={witness}")

    examples = (
        BlockArrayInstance(1, 1),
        BlockArrayInstance(1, 2, horizontal_gap=4),
        BlockArrayInstance(2, 2),
    )
    for instance in examples:
        finding = assess(instance, closure)
        print(
            f"block-array {instance.rows}x{instance.columns} "
            f"gaps=({instance.horizontal_gap},{instance.vertical_gap}): "
            f"reachable={finding.reachable_in_supplied_graph} witness={finding.witness}"
        )

    if not all(result.valid for result in verifications):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
