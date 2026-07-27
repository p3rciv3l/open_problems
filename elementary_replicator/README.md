# Problem 8: a precise Conway Life replicator target

This directory concerns only Conway Life, B3/S23. “Elementary” has no accepted
mathematical meaning here, so it is not used as a predicate.

## A theorem-grade predicate

Let `Phi` be the global B3/S23 map. A finite pattern is a **certified
macro-replicator** if there are:

- a finite nonempty macro-pattern `P`, lattice vector `d`, period `tau`, and
  finite interaction radius `r`;
- a binary radius-`r` cellular automaton `F` whose orbit from one live
  macrocell has unbounded support;
- an encoding `E(a) = union {P + i*d : a(i)=1}` for every finitely supported
  macro-configuration `a`;
- a bounded protective region around each output tile;

such that, for every one of the `2^(2r+1)` local input words, direct Life
simulation for `tau` ticks produces exactly the `F` output tiles in the
corresponding protective regions, produces no cells outside them, and no
input outside that local word can enter a protected output region during the
test. Equivalently, the verified local identities imply

`Phi^tau(E(a)) = E(F(a))`

for every finitely supported `a`. Induction then gives
`Phi^(n*tau)(E(a)) = E(F^n(a))`; unbounded support of `F^n({0})` is the
replicator theorem. The local-context confinement is the required
noninteraction invariant. It does **not** assume that copies evolve
independently: parity replicators require controlled interaction and
annihilation.

## Why strict independent doubling must be dropped

A different tempting definition is impossible. Suppose a nonempty finite
seed of population `m` and bounding box `w` by `h` yielded `2^n` disjoint
copies after `nT` ticks, with every child independently doubling after the
same fixed period `T`. It would require `m*2^n` live cells. Radius-one finite
propagation confines all descendants to a box of at most

`(w + 2nT)(h + 2nT)`

cells. Exponential growth eventually exceeds this quadratic bound. Therefore
no finite B3/S23 pattern can satisfy fixed-period binary branching together
with indefinite pairwise noninteraction. This is rule-independent for every
two-dimensional finite-radius cellular automaton.

The theorem-grade target must instead specify a macro-rule recurrence,
increasing generation intervals, or construction machinery. “Produces two
copies once” is not an inductive replicator theorem.

## Finite-phase branching obstruction

The same finite-speed argument excludes a substantially broader class,
including reflection-changing and phase-changing macrotiles whose daughters
may interact arbitrarily between sampling times.

**Theorem (finite-phase superquadratic obstruction).** Let `G` be a
two-dimensional radius-`rho` cellular automaton with a quiescent state. Start
from a finite pattern in a `w` by `h` box. Suppose that at every time `n*T`
the complete configuration is exactly a pairwise-disjoint union of finite
nonempty macrotiles from a fixed finite phase alphabet `Q` (reflections and
rotations may be separate phases). If `c_n` is the number of macrotiles at
that time, then

`c_n <= (w + 2*rho*T*n)(h + 2*rho*T*n)`.

In particular, this class contains no system for which `c_n` grows
superquadratically.

**Proof.** Quiescence and radius `rho` imply inductively that after `n*T`
steps every nonquiescent cell lies in the initial bounding box enlarged by
`rho*T*n` in each direction. That box contains exactly
`(w + 2*rho*T*n)(h + 2*rho*T*n)` sites. Every endpoint macrotile is nonempty,
and endpoint macrotiles are pairwise disjoint, so selecting one
nonquiescent cell from each gives an injection from the `c_n` macrotiles
into those sites. The displayed inequality follows. Its right side is a
quadratic polynomial in `n`, which excludes superquadratic `c_n`. `QED`

**Corollary (context-free finite-phase substitutions).** Suppose in addition
that one macro-generation replaces each phase `q` by a fixed finite multiset
of daughter phases, that endpoint daughters are pairwise disjoint globally,
and that this identity repeats after the fixed time `T`. Let the nonnegative
integer substitution matrix be `M`, with `M[q,r]` daughters of phase `r`
from phase `q`. If the singleton-reachable part of `M` has spectral radius
greater than one, no such Life system exists.

Indeed, exact phase counts are `e_q M^n`. Perron--Frobenius growth on the
reachable supercritical component makes their sum exponential (a finite
transient before that component is irrelevant), contradicting the theorem.
This covers any finite number of reflected/rotated phases, unequal offspring
counts, transient phases, and all interactions during a macro-period. It does
not assume that daughters evolve independently. The necessary escape hatch
is endpoint cancellation/coalescence or another context-dependent macro-rule,
such as parity, or non-fixed generation times. Thus merely adding a reflected
second phase to clean doubling cannot work.

`branching_certificate.py` performs only exact integer recurrence and
light-cone arithmetic. The committed certificate uses the two-phase
substitution `A -> B`, `B -> A+B`; reproduce and independently verify it:

```sh
python -m elementary_replicator.branching_certificate \
  --output elementary_replicator/certificates/two_phase_fibonacci.json
python -m elementary_replicator.branching_certificate \
  --verify elementary_replicator/certificates/two_phase_fibonacci.json
```

The certificate is not claimed as a Life construction or a finite-horizon
replicator. It is a machine-checkable finite contradiction for one
representative member of the theorem's infinite excluded class.

## Local macro-rule SAT exclusion

`sat_macro_rule.py` searches the theorem-grade predicate directly for a
one-phase horizontal tile. A geometry `(w,h,L,T)` has an unknown nonempty
minimal-box pattern `P` in `[0,w-1] x [0,h-1]`, horizontal macro pitch `L`,
and period `T`. The integer plane is partitioned into width-`L` output
windows, one per macro site.

For each of the eight radius-one macro contexts `(left,centre,right)`, the SAT
instance starts Life from the corresponding union of copies at translations
`-L`, `0`, and `L`. At time `T`, the complete central output window, including
the full vertical light cone, must be exactly `P` or empty according to the
selected macro-rule bit. Interactions in contexts with two or three input
tiles are simulated normally; independent evolution is not assumed. A
geometric precondition proves that sites outside the three-cell context
cannot reach the central window in `T` ticks.

Consequently, a satisfying tile would prove the local identity for every
finite macro-configuration. Induction would be a complete Life replicator
theorem, not evidence from one doubling event.

The searched macro rules are additive ECA rules 60, 90, 102, and 150. Each
has an unbounded singleton orbit: over `GF(2)`, its update is multiplication
by a Laurent polynomial with at least two terms, and at times `2^k` the
Frobenius identity scales the distinct exponents by `2^k`.

The exact UNSAT scopes are:

- all `1 <= w,h <= 4`, `L=w+1`, `T=L`, for all four rules: 64 instances;
- all `1 <= w,h <= 3`, `L=w+2`, `T in {L,L+1}`, for all four rules:
  72 instances.

Vertical tile reflection is removed in every scope. Horizontal reflection is
also removed for symmetric rules 90 and 150. The direct B3/S23 verifier
independently enumerates all tiles in the `2x2`, `L=3`, `T=3` subscopes and
agrees with all four SAT exclusions. No macro tile was found.

This exclusion allows parity-style controlled collisions but is deliberately
limited to one translated phase. The pre-pulsar's reflected second child
shows why a next search should admit a two-phase tile alphabet with a
reflection-changing transition; its close spacing still requires controlled
collision rather than independent copies.

## Bounded SAT exclusion

`sat_clean_doubling.py` encodes B3/S23 exactly. For each scope, the unknown
nonempty seed touches all four sides of its minimal `w` by `h` box. At time
`T`, the complete finite configuration must equal exactly two translated
copies whose bounding boxes are disjoint; no debris is allowed. Rotation
symmetry restricts to `h <= w`; lex-leader constraints remove horizontal and
vertical seed reflections. Finite propagation bounds both translations to
`[-T,T]^2` and the encoded spacetime to the expanding light cone.

The completed scope

- covers every minimal box with `1 <= h <= w <= 6`;
- covers every `1 <= T <= 4`;
- checks 67,874 geometrically possible translation pairs;
- is UNSAT throughout.

The independently exhaustive direct simulator agrees on every seed through
`4x4` and `T <= 4`. Install `requirements.txt` and reproduce a smaller SAT
scope with:

```sh
python -m elementary_replicator.sat_clean_doubling --max-side 4 --max-time 2
```

Reproduce the independent explicit-state scope with:

```sh
python -m elementary_replicator.direct_search --max-side 4 --max-time 4
```

## Failed-replicator mechanisms

The canonical pre-pulsar

`bo5bob$3o3b3o!`

has eight cells in a `9x2` box. At generation 15 it is exactly two
debris-free copies, but one is vertically reflected: the child boxes are at
vertical offsets `-3` and `4`. Evolving those children together for another
15 ticks gives 48 cells; evolving them separately and taking the union gives
26 cells, with a 42-cell symmetric difference. Their light cones overlap, so
the first event supplies no inductive separation lemma. There are only five
dead rows between the children; keeping their radius-one light cones disjoint
for the next 15 ticks would require at least 30. A repair must therefore add
at least 25 rows of clean displacement, not merely suppress a spark. Tubs
suppress one half to make shuttles; they do not repair separation. Skewing
changes the phase geometry but remains unstable.

The pi-heptomino `3o$obo$obo!` has two translated pi subsets at generation
26, at offsets `(0,-8)` and `(0,-2)`, but the full population is 67 rather
than 14. The 53 debris cells alter the putative children immediately on the
next tick. Its child boxes have only three intervening rows, versus 52 needed
for 26 ticks of strict separation. This is a dirty local duplication inside
an explosion, not a candidate for the clean or macro-rule predicates.

Sources:

- [LifeWiki: Replicator](https://conwaylife.com/wiki/Replicator)
- [LifeWiki: Pre-pulsar](https://conwaylife.com/wiki/Pre-pulsar)
- [LifeWiki: Pi-heptomino](https://conwaylife.com/wiki/Pi-heptomino)
