# Handoff 05: Strong Unique Father

## Target

Strengthen the solved Unique Father theorem. The main open formulations ask
for a finite still life whose forced predecessor patch contains all of its
live cells, or every cell in the convex hull of its live population.

## Current frontier

Salo and Törmä found a finite still life containing a self-enforcing patch:
every predecessor already contains that patch in the same position. This
settled one precise interpretation and produced an unsynthesizable still life.
It did not force the complete stabilized object. Subsequent searches reduced
the populations of known unsynthesizable stabilizations, but population
minimization is different from strengthening the quantifiers.

## Recommended attack

1. Reproduce `gol-agars` enumeration and finite-patch forcing checks.
2. Score candidates by forced-domain coverage of a stabilization, not by raw
   population.
3. Jointly search an agar patch and a finite stabilization so that every live
   stabilization cell lies in the maximal self-enforcing subset.
4. For convex-hull forcing, include dead hull cells explicitly in the target
   domain.
5. Minimize only after a strong witness exists.

An alternating SAT loop is natural: find a proposed stabilization, ask for a
predecessor differing in the required domain, and enlarge or modify the
forcing patch using that counterexample.

## Evidence required

- A complete RLE or coordinate assignment for the finite still life.
- A precise forced domain and statement of which strong variant it satisfies.
- An independently checkable UNSAT encoding showing that no predecessor
  differs on that domain.
- Direct simulation proving the finite pattern is stable.

## Traps

- Calling the 2022 theorem the strongest possible Unique Father statement.
- Optimizing population while forced live cells remain outside the patch.
- Ignoring dead cells when claiming convex-hull coverage.
- Restricting predecessors to finite support or dead boundaries without
  proving that restriction is sound.

## Starting points

- Salo–Törmä, [What Can Oracles Teach Us About the Ultimate Fate of
  Life?](https://arxiv.org/abs/2202.07346)
- [`gol-agars`](https://github.com/ilkka-torma/gol-agars)
- LifeWiki [Unique father problem](https://conwaylife.com/wiki/Unique_father_problem)
