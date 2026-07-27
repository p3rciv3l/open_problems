# Handoff 10: Finite basis for glider synthesis

## Target

Determine whether constants bound both the number of gliders per synthesis
stage and the spatial extent of each stage for every synthesisable still life.
Equivalently, seek a finite set of bounded local rewrite forms sufficient for
all synthesisable still lifes.

## Current frontier

All strict still lifes through population 23 have explicit syntheses.
Self-enforcing still lifes prove that some still lifes are not synthesisable,
so the theorem must be conditional on synthesisability. Existing component
transfer tools already treat many synthesis steps as local rewrites, but no
uniform finite-basis theorem is known.

## Recommended attack

1. Normalize known synthesis components by translation, dihedral symmetry,
   glider phase, unchanged context, and exact affected box.
2. Build a directed rewrite graph on complete small still-life censuses.
3. Measure the smallest glider-count and box-size cutoffs that preserve
   reachability of every known synthesisable target.
4. Extract missing local motifs from targets that require larger cutoffs.
5. Seek a structural decomposition of arbitrary synthesisable still lifes
   into bounded interfaces, rather than extrapolating census data.

A useful intermediate artifact is a minimal candidate basis with a
machine-checkable application semantics and coverage report.

## Evidence required

- Canonical encodings of stages, gliders, timing, and unchanged context.
- Independent simulation of every rewrite rule.
- Explicit constants proposed for the basis.
- A mathematical decomposition showing every synthesisable still life admits
  a sequence over the basis; finite census closure alone is not enough.

## Traps

- Forgetting that the final theorem excludes unsynthesisable still lifes.
- Treating a component as local when distant debris or timing participates.
- Counting semantically identical translated components as new basis rules.
- Inferring universal constants from populations through 23.

## Starting points

- The 2024 “finitude of spanning set of synthesis stages” formulation on the
  LifeWiki [problem index](https://conwaylife.com/wiki/Problem)
- Shinjuku component templates, `transfer.py`, and Stomp
- M. V. R., [All 23-Bit Still Lifes Are Glider
  Constructible](https://mvr.github.io/posts/xs23.html)
