# Handoff 11: Minimization and record certification

## Target

Turn selected Life records from “smallest found” into “proved minimal,” and
make both witnesses and lower-bound proofs independently replayable. Choose
one sharply defined record; this category is a methodology, not a single
optimization problem.

## Current frontier

Life search programs routinely produce impressive witnesses, but exclusion of
all smaller candidates is less standardized. SAT has certified minimum
Gardens of Eden, still-life stabilizations, spaceships, and predecessor
properties in bounded scopes. Many results still depend on custom code,
solver trust, undocumented symmetry assumptions, or unavailable search logs.

## Recommended attack

Start with a record whose validity predicate is local and whose search box is
modest:

1. Publish a canonical instance schema and symmetry convention.
2. Generate an attaining witness and verify it with a tiny independent
   simulator.
3. Encode “a better witness exists” as CNF without solver-specific shortcuts.
4. Emit DRAT or LRAT for UNSAT and validate it with a second checker.
5. Bundle a manifest containing hashes, tool versions, and exact commands.

Good first targets include small predecessor exclusions, exact-period
oscillators in fixed boxes, and minimum populations under fixed geometry.
Avoid an enormous fashionable record until the certificate pipeline works.

## Evidence required

- A precise ordering: population, bounding box, period, clearance, or a stated
  lexicographic combination.
- Completeness of symmetry breaking, with a proof that no orbit is discarded.
- Independent witness replay.
- Independently checked UNSAT for every strictly better objective value.
- Reproducible artifact hashes and no dependence on private databases.

## Traps

- Calling the best result returned before timeout “optimal.”
- Verifying the witness but not the lower bound.
- Using an optimization solver whose final bound has no proof artifact.
- Hiding assumptions in preprocessing or candidate generation.
- Mixing incomparable record metrics.

## Reusable artifacts

The repository's `life_density` package demonstrates bounded optimization and
independent witness checking, but its Z3 upper bounds are not standalone
certificates. Replacing that trust boundary with CNF plus DRAT/LRAT is a
well-scoped first project.

## Starting points

- Beer, [Symmetry in Gardens of
  Eden](https://www.combinatorics.org/ojs/index.php/eljc/article/view/v20i3p16)
- CaDiCaL proof logging and DRAT/LRAT checkers
- HOL4's verified Life work for a stronger long-term formalization path
