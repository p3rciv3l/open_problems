# Handoff 03: Still-life finitization

## Target

Decide whether every finite window of every infinite still life can be
preserved inside some finite still life by adding a finite stabilizing
exterior. A counterexample must rule out every finite margin; a positive
solution needs a general construction.

## Current frontier

The weaker Coolout conjecture is false: a locally still-life-compatible
partial pattern need not admit any stabilization. Finitization remains open
because its core is promised to come from an actual infinite still life.
Known examples show that the required stabilizing margin is not bounded by a
universal constant.

## Recommended attack

Use SAT to compute the minimum stabilizing annulus around windows cut from
periodic still-life agars:

1. Canonicalize an agar and a sequence of growing windows.
2. For margin `m`, fix the core, require all cells outside the finite support
   to be dead, and encode exact stability.
3. Preserve UNSAT certificates for margins below the first solution.
4. Search the resulting data for a conserved boundary charge or forced defect
   whose displacement grows with window size.

The computational goal is a parametric family. If minimum margins grow, turn
the observed boundary state into a finite automaton or transfer matrix and
prove the growth law. For a negative answer, seek a promised infinite still
life whose finite cuts force a defect to continue outward forever.

## Evidence required

- Exact definitions of the fixed core, free annulus, and dead exterior.
- Independently replayable finite stabilizations.
- Proof-producing UNSAT for excluded margins.
- For an unbounded conclusion, an invariant or automaton argument covering
  every larger annulus.

## Traps

- Using a core that is merely locally consistent rather than contained in an
  infinite still life.
- Reporting a large minimum margin as evidence that no finite margin exists.
- Forgetting dead cells in the preserved window; a window is a full
  assignment, not only its live population.
- Letting disconnected still lifes outside the annulus contaminate the
  definition of support.

## Starting points

- LifeWiki [problem index](https://conwaylife.com/wiki/Problem)
- Chu–Stuckey, *A Complete Solution to the Maximum Density Still Life
  Problem*, for transfer and wastage techniques
- Periodic still-life agars as controlled core families
