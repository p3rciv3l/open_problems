# Handoff 07: Universal single-glider-proof object

## Target

Find a bounded object such that every nonempty glider approaching from
infinity, in every direction, phase, and lane that interacts with it, is
destroyed and the object's eventual evolution is unaffected.

## Current frontier

Many eaters absorb selected lanes, and finite constructions can protect an
arbitrarily wide one-directional highway. No bounded target is known to
recover from every single-glider collision. The problem is strictly weaker
than the Immovable Object problem because the adversary is one glider, but the
eventual-recovery clause still needs proof.

## Recommended attack

1. Define a canonical finite or periodic target and recovery equivalence.
2. Enumerate the finite set of lanes and phases whose glider light cones
   intersect the target's bounding box.
3. Simulate each collision until it either escapes, enters a certified basin,
   or exceeds a conservative horizon.
4. Use SAT or component searches to add catalysts for failing lanes while
   continuously rechecking previously solved lanes.
5. Search symmetric targets to reduce lane classes, but verify the symmetry
   reduction formally.

The best intermediate metric is a complete lane table with exact outcomes,
not a percentage sampled from offsets.

## Evidence required

- Proof that all more distant lanes are noninteracting.
- Exhaustive coverage of four directions, four glider phases, and all
  interacting offsets modulo translation.
- For each lane, a replayable trace to the original target phase plus only
  outgoing debris allowed by the definition.
- A certified settling or recovery criterion; a finite quiet-looking horizon
  is insufficient.

## Traps

- Ignoring gliders that graze temporary sparks outside the initial box.
- Counting conversion to harmless still-life junk as recovery when the target
  must be unchanged.
- Missing target phase if the candidate itself oscillates.
- Testing only one glider color or orientation.

## Starting points

- LifeWiki [glider destruction](https://conwaylife.com/wiki/Glider_destruction)
- LifeWiki [single-glider-proof problem](https://conwaylife.com/wiki/Problem)
- Existing eater and eater-chain lane tables as seed components
