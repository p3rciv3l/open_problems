# Conway Life open-problem research map

This document separates theorem-sized questions from computational record
searches. A finite computation can settle a bounded instance, find a witness,
or produce a checkable certificate; it cannot by itself establish an
unbounded claim.

## Current status and plausible attacks

| # | Problem | Current boundary | Useful next computation |
|---|---|---|---|
| 1 | Random initial conditions | Even basic asymptotic questions for an i.i.d. Bernoulli configuration remain open. Gotts obtained rigorous sparse-regime, finite-time results; simulations at ordinary densities are empirical. | Reproducible finite-size scaling, rare-event logging, and exact enumeration of small light cones. The purpose is to formulate sharp conjectures and identify counterexamples, not to extrapolate a theorem from a torus. |
| 2 | Exact complexity of the limit set | Salo and Törmä proved that the language of the limit set is PSPACE-hard, non-sofic, and not block-gluing. They explicitly leave open whether its language reaches the computability-theoretic upper behavior possible for cellular automata. | Mechanize reductions for stronger lower bounds, or search for finite backward-forcing gadgets that implement quantified or nonhalting computations. |
| 3 | Still-life finitization | It is unknown whether every finite window cut from an infinite still life can be embedded unchanged in a finite still life. Stabilizing margins can be arbitrarily large. | Encode annular stabilization as SAT and enumerate minimal margins for periodic and adversarial cores. A family with a provable invariant is more valuable than isolated large margins. |
| 4 | Maximum density of an oscillating universe | The conjectured maximum average spacetime density is \(1/2\). The published community upper bound is \(1176/2087\), about 0.56349. | Optimize exact periodic spacetime configurations on finite tori, then use their dual constraints to search for translation-invariant local inequalities. A proof must sum to a global bound without boundary terms. |
| 5 | Strong Unique Father | A finite still life containing a self-enforcing patch was constructed in 2022. Stronger variants requiring the forced patch to contain all live cells, or every cell in their convex hull, remain open. | Reproduce the `gol-agars` SAT method, then optimize the relationship between the forced patch and its finite stabilization rather than population alone. |
| 6 | Immovable Object | It is unknown whether a bounded pattern can protect the state of a central cell forever against every exterior completion. | Bounded-time adversarial SAT/model checking can eliminate candidates. A positive result needs an inductive shield invariant; brute-force survival for a large time is not evidence of forever. |
| 7 | Universal single-glider-proof object | No bounded target is known to absorb every glider lane and phase and eventually return to its original evolution. | Enumerate all lanes that intersect a candidate's finite influence cone, simulate through a conservative recovery horizon, and use SAT to synthesize repairs for the remaining lanes. Completeness requires a proof that more distant lanes do not interact. |
| 8 | Finite elementary replicator | Life has engineered replicators and failed elementary replicators, but no finite elementary pattern is known that repeatedly copies itself without constructor circuitry. | Search constrained expanding spacetime cones for a seed whose separated descendants are exact translates. Collision-free continuation must be verified inductively, not merely for the first copying event. |
| 9 | Wave and spaceship speeds | Finite spaceships obey the standard directional speed limits. Orthogonal waves strictly between \(c/2\) and \(c\) remain open; period-at-most-10 possibilities except a near-complete \(6c/10\) search have been eliminated. | Reproduce width-increasing wavefront SAT searches at \(3c/5\), retaining UNSAT certificates and checking whether partial fronts converge to a repeatable boundary state. |
| 10 | Finite basis for glider synthesis | A 2024 formulation asks whether bounded glider count and bounded interaction boxes suffice at each stage of every synthesisable still life. All strict still lifes through population 23 are known to be synthesisable, while self-enforcing still lifes show that not every still life is. | Normalize known synthesis components into local rewrite rules and measure closure on complete small still-life censuses. Missing rewrites identify concrete basis candidates; finite census coverage alone cannot prove universality. |
| 11 | Minimization and certification | Many records have witnesses but no independently replayable minimality proof. SAT-based predecessor, oscillator, spaceship, and still-life searches are natural targets for proof-producing workflows. | Standardize instance encodings, witnesses, independent simulators, and DRAT/LRAT-style UNSAT artifacts. Separate “smallest found” from “proved minimal” in machine-readable results. |

## Why oscillator density is the first target

The density problem has a local rule, a linear objective, a sharp conjectured
value, and a nontrivial gap to the best upper bound. It supports two
complementary computations:

1. Exact finite-torus optimization gives reproducible lower bounds and tests
   candidate structural lemmas.
2. Local-inequality search can, in principle, return rational coefficients
   whose exhaustive verification and telescoping sum constitute a proof.

Finite-torus optima are not automatically bounds for the infinite-plane
problem. They are a laboratory for discovering the local statement that would
be.

## Evidence standard

- **Witness:** replay every generation with a small independent simulator.
- **Bounded optimum:** provide both an attaining witness and an independently
  checkable UNSAT or optimization certificate for all better values.
- **Infinite theorem:** state the finite local lemma, exhaustively verify its
  cases, and show algebraically how translated copies imply the global claim.
- **Empirical claim:** record seeds, dimensions, boundary conditions, stopping
  rules, and uncertainty; do not silently promote finite-size behavior to an
  asymptotic statement.

## Primary references

- N. Brown et al., [Conway's Game of Life is
  Omniperiodic](https://arxiv.org/abs/2312.02799), 2023.
- V. Salo and I. Törmä, [What Can Oracles Teach Us About the Ultimate Fate of
  Life?](https://arxiv.org/abs/2202.07346), 2022, with
  [`gol-agars`](https://github.com/ilkka-torma/gol-agars).
- N. Johnston and D. Greene, [Conway's Game of Life: Mathematics and
  Construction](https://conwaylife.com/book/), 2022.
- Noam Elkies, [The still-Life density problem and its
  generalizations](https://arxiv.org/abs/math/9905194), 1999.
- The maintained LifeWiki [open-problem
  index](https://conwaylife.com/wiki/Problem) and
  [density summary](https://conwaylife.com/wiki/Density).
