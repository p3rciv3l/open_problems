# Handoff 08: Finite elementary replicator

## Target

Find a finite, non-engineered Life pattern that repeatedly produces separated
copies of itself indefinitely, or prove a meaningful restricted class cannot
contain one. State the replication definition before searching: number and
placement of children, permitted debris, generation time, and whether the
parent survives.

## Current frontier

Life supports constructor-based replicators, and infinite or bounded-axis
backgrounds can emulate parity-rule replication. No finite elementary
replicator is known. The pre-pulsar and pi-heptomino sequences create apparent
copies once, but later interactions prevent indefinite replication.

## Recommended attack

Search backward from a desired two-child state:

1. Choose a symmetry, replication vector, generation `T`, and protected
   separation corridor.
2. Encode a finite seed whose generation-`T` state contains two exact
   translated seeds and no cells capable of crossing between their future
   cones.
3. Minimize seed and corridor only after feasibility.
4. Prove that the children evolve independently and repeat the same event.

The noninteraction lemma is the leverage. If each child has a forward cone
confined to a region that scales away from the others, one verified copying
cycle implies indefinite replication by induction.

## Evidence required

- Complete initial pattern and exact generation of replication.
- Independent simulation of the full first cycle.
- Geometric proof that every child has the same environment required by the
  parent.
- An inductive separation argument ruling out later cross-generation
  collisions and accumulated debris.

## Traps

- Declaring success after one copying event.
- Allowing hidden constructor circuitry while using “elementary.”
- Comparing children only up to population or bounding box instead of exact
  translation/reflection under the stated definition.
- Ignoring debris whose light cone reaches descendants much later.

## Starting points

- LifeWiki [replicator](https://conwaylife.com/wiki/Replicator)
- Pre-pulsar and pi-heptomino failed-replicator mechanisms
- Expanding spacetime-cone SAT encodings and exact-period search techniques
