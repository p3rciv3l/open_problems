# Handoff 06: Conway's Immovable Object problem

## Target

Find a bounded pattern and a distinguished central cell whose state never
changes, for all time, under every possible assignment outside the pattern;
or prove that no such bounded pattern exists.

## Current frontier

The problem has been open since 1972. Ordinary stable objects, eaters, and
large engineered walls do not satisfy the quantifiers: the exterior is
adversarial, can be infinite, and can coordinate attacks forever.

## Recommended attack

Treat this as safety verification rather than pattern search:

1. For a fixed candidate and time horizon `T`, encode exterior cells in the
   backward light cone as universally adversarial inputs.
2. Use SAT to find the earliest trace that flips the central cell.
3. Learn structural reasons from counterexamples and synthesize candidate
   shells with quantified Boolean solving or counterexample-guided repair.
4. Search for a finite inductive invariant on concentric boundary states.

A positive proof likely resembles a shield automaton: every reachable boundary
state maps to another safe boundary state while preserving a smaller protected
core. A finite closed set of such states would discharge the infinite time
quantifier by induction.

## Evidence required

- Exact convention for whether the central cell starts live or dead.
- An invariant containing the initial pattern and closed under every exterior
  input.
- Exhaustive, machine-checkable verification of each invariant transition.
- A short induction connecting the finite transition check to all time.

Bounded survival is only a candidate filter, regardless of the horizon.

## Traps

- Simulating random attacks instead of universally quantifying the exterior.
- Assuming attacks arrive as separated spaceships or gliders.
- Fixing the exterior once when the mathematical quantifier permits an
  arbitrary initial infinite configuration whose signals arrive later.
- Mistaking a very slow failure for an invariant.

## Starting points

- LifeWiki [Lifeline Volume 7](https://conwaylife.com/wiki/Lifeline_Volume_7)
- Symbolic model checking and safety-game algorithms
- Self-enforcing agar rings as possible one-way barriers, with no assumption
  that their known backward-forcing property implies forward invulnerability
