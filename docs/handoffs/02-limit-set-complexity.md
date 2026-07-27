# Handoff 02: Exact complexity of Life's limit set

## Target

Classify the language of Life's limit set: given a finite pattern, determine
whether it occurs in a configuration having arbitrarily long predecessor
chains. The useful deliverable is a sharper completeness or hardness theorem,
not another difficult-looking family of reverse-Life instances.

## Current frontier

Salo and Törmä proved that the language is PSPACE-hard, that the limit set is
non-sofic, and that Life never reaches its limit set. Their paper explicitly
leaves open whether the language attains the higher arithmetical complexity
possible for cellular-automaton limit sets. Life's computational universality
does not settle this: the reduction must survive arbitrary surrounding cells
and unbounded backward depth.

## Recommended attack

1. Reproduce the `gol-agars` self-enforcing patches and its PSPACE reduction.
2. Build backward-forcing wires whose validity is quantified over every
   exterior completion, not only a dead background.
3. Encode a machine whose arbitrarily deep predecessor chains correspond to
   nontermination or well-foundedness.
4. State the exact many-one reduction and its input-size growth before
   optimizing gadgets.

The key design object is a finite patch that forces both data and timing
through every predecessor. Self-enforcing agar boundaries are more promising
than ordinary glider circuitry because external junk cannot silently supply
an alternative computation.

## Evidence required

- A finite formal definition of the source decision problem and reduction.
- Machine-checkable one-step forcing certificates for every gadget.
- A compositional proof that gadget certificates survive tiling and routing.
- Explicit polynomial bounds on output-pattern extent.

SAT output can establish finite gadget lemmas. It cannot establish the
unbounded reduction without the surrounding mathematical argument.

## Traps

- Confusing finite-support predecessors with arbitrary infinite predecessors.
- Treating ordinary construction universality as predecessor universality.
- Claiming completeness from hardness without proving the matching upper
  bound under a precise encoding.
- Relying on a fixed empty environment where the theorem quantifies over all
  completions.

## Starting points

- Salo–Törmä, [What Can Oracles Teach Us About the Ultimate Fate of
  Life?](https://arxiv.org/abs/2202.07346)
- [`gol-agars`](https://github.com/ilkka-torma/gol-agars)
- Salo–Törmä, *Computing backwards with Game of Life, part 1*
