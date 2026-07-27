# Handoff 09: Possible wave and spaceship speeds

## Target

Classify attainable velocities for finite spaceships and infinite waves, with
special focus on an orthogonal wave strictly between `c/2` and `c`. The
concrete current target is `3c/5`, commonly searched as `6c/10`.

## Current frontier

Finite Life spaceships obey the standard directional speed limits: no
orthogonal spaceship exceeds `c/2`, and analogous taxicab bounds apply in
other directions. Infinite waves can move faster in a supporting medium.
No orthogonal wave speed strictly between `c/2` and `c` is known. Period-at-
most-10 alternatives have been eliminated except that `6c/10` produced
notably close partial fronts.

## Recommended attack

1. Recover the exact prior search constraints and reproduce a small excluded
   width.
2. Encode a translating spacetime strip at displacement 6 and period 10.
3. Increase width while recording boundary states of near-complete partials.
4. Detect repeated boundary states that permit pumping to an infinite wave.
5. For failed widths, retain proof-producing UNSAT certificates.

Search both primal patterns and a finite-state transfer graph of compatible
columns. A directed cycle in the correct transfer graph can be a concise
existence proof for an infinite wave; absence of cycles can certify a bounded
width class.

## Evidence required

- Exact velocity, period, displacement, background, and wave equivalence.
- A finite fundamental spacetime domain plus a checked tiling or pumping
  argument.
- Independent simulation across seams.
- For nonexistence claims, a complete width/period scope and checkable UNSAT
  or transfer-graph exhaustion.

## Traps

- Applying finite-spaceship speed limits to waves in a supporting medium.
- Reporting a long partial front without a repeatable boundary state.
- Accidentally finding a lower fundamental period or a differently
  interpreted displacement.
- Omitting phase shifts in the background agar.

## Starting points

- LifeWiki [wave](https://conwaylife.com/wiki/Wave)
- LifeWiki [spaceships](https://conwaylife.com/wiki/Spaceships)
- The ConwayLife wave-completion and level-wave-speed discussions
