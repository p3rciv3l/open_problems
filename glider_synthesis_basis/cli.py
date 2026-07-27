"""Print reproducible bounded findings for the built-in corpus."""
from .analysis import bounded_closure
from .block_arrays import BlockArrayInstance, assess, construct_spaced_block_array
from .corpus import (
    REWINDABLE_TWO_GLIDER_CORPUS,
    candidate_basis_report,
    corpus_population_spectrum,
)
from .published import certify_two_row_extension_theorem
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

    print(
        f"rewindable two-glider corpus: {len(REWINDABLE_TWO_GLIDER_CORPUS)} "
        f"reactions, output populations={corpus_population_spectrum()}"
    )
    candidate = candidate_basis_report()
    print(
        f"B8 candidate exact closure: {candidate.exact_contexts_from_empty} contexts, "
        f"universal_claim={candidate.universal_claim}"
    )
    spaced = construct_spaced_block_array(
        BlockArrayInstance(3, 4, horizontal_gap=6, vertical_gap=6)
    )
    print(
        f"certified spaced 3x4 array: {spaced.glider_count} gliders, "
        f"output_population={len(spaced.move.output_context)}"
    )
    theorem = certify_two_row_extension_theorem()
    print(
        f"published 2xn extension: directly checked "
        f"{theorem.directly_verified_widths[0]}.."
        f"{theorem.directly_verified_widths[-1]}, "
        f"locality_margin={theorem.locality_margin}"
    )

    if not all(result.valid for result in verifications):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
