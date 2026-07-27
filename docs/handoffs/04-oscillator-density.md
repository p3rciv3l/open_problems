# Handoff 04: Maximum density of an oscillating universe

## Target

Prove or refute that every spatially periodic, temporally periodic Life
configuration has average spacetime density at most `1/2`. The best outcome is
a rational local certificate whose translates telescope to the global bound.

## Current frontier

Density `1/2` is attained. The maintained community upper bound is
`1176/2087`, approximately `0.56349`. The repository's
`life_agar_certificate` experiment gives an exact, dependency-free
certificate for `8/13` and a balanced 57-neighborhood dual witness proving
that no radius-one, one-step full-face potential can improve that value.

## Recommended attack

Build a hierarchy of larger local-potential linear programs:

1. Add temporal depth before indiscriminately increasing spatial radius.
2. Use strip or face potentials whose translated terms cancel exactly.
3. Generate local spacetime blocks lazily with SAT-based separation.
4. Solve numerically, rationalize a sparse dual, then verify every local
   inequality with exact arithmetic.
5. First beat `8/13`; next reproduce `1176/2087`; only then target `1/2`.

Finite-torus optimization is useful for finding tight motifs and falsifying
candidate inequalities. It does not upper-bound the infinite problem.

## Evidence required

- The explicit local inequality and a proof of telescoping cancellation.
- Exhaustive verification over all locally valid spacetime blocks.
- Rational coefficients and a dependency-free verifier.
- If optimality within an ansatz is claimed, a feasible balanced dual
  distribution with matching objective.

## Traps

- Assuming locally consistent block marginals extend to a global Life orbit.
- Calling a floating-point LP optimum a proof.
- Omitting twisted spacetime boundary cases while claiming results for moving
  periodic patterns.
- Spending compute on larger tori without extracting a local lemma.

## Reusable artifacts

- `life_agar_certificate`: exact `8/13` certificate, LP generator, and verifier.
- `life_density`: exact bounded torus optimizer and independent witness
  simulator; upper bounds currently remain under Z3 trust.

## Starting points

- LifeWiki [density summary](https://conwaylife.com/wiki/Density)
- Elkies, [The still-Life density problem and its
  generalizations](https://arxiv.org/abs/math/9905194)
