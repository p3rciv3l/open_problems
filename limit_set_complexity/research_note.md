# Exact complexity: status and missing gadget

For Life's global map `g`, the limit set is
`Omega(g) = intersection_n g^n({0,1}^{Z^2})`. A finite pattern `p` is in its
language exactly when it occurs in every `g^n({0,1}^{Z^2})`: the reverse
direction follows from compactness of the nested closed cylinder
intersections. Nonmembership therefore has a finite witness (some depth and
finite predecessor window with no solution), so the language is in
`Pi^0_1`.

Salo and Törmä prove that this language is PSPACE-hard (Theorem 2), and
explicitly leave open whether it reaches the `Pi^0_1` upper bound. Nothing in
this directory improves that theorem.

## What the experiment establishes

`forcing.py` verifies a finite core of their Lemma 17. A `30 x 27` köynnös
output patch forces one central `6 x 3` predecessor period, for every spatial
phase. Since this local statement can be translated over the plane, the full
periodic agar has only itself as a one-step predecessor. The SAT check is
robust to arbitrary predecessor values at the edge: only cells in the exact
radius-one predecessor rectangle are variables, and no periodicity is imposed
on them.

That is a rigid backward background, not an unbounded computation. Repeating
the forced tile only repeats the same fixed point; it does not encode a
machine, a growing tape, or a halting obstruction.

## Attempted composition with published backward circuitry

Salo and Törmä's later circuit construction proves one-step block-map
universality. In its simulation diagram, an encoded circuit layout is on the
**output** side of Life, while a Life predecessor decodes to a satisfying wire
assignment. The predecessor is not required to be another encoded circuit
layout. The authors call their result semiweak universality and explicitly
state that free choices in the predecessor leave them no control over a
second-order predecessor.

This is a type mismatch, not merely a missing Boolean gate. Even the stronger
one-step property they leave open (a bijection between predecessors and valid
assignments) would remove extraneous first preimages but would not by itself
make the predecessor belong to the output encoding needed for another round.
Iteration needs a closed, temporally composable encoding:

```text
encoded machine state at time t
       <-- every Life predecessor --
encoded machine state at time t+1.
```

A kynnös ring does not repair this mismatch. It forces the same annulus at the
same coordinates in each predecessor, but places no requirement that the
interior's first-preimage wire assignment is a circuit layout for the next
inverse step.

## Fixed-ring obstruction

The ring gives a stronger exact negative statement.

**Finite-trap lemma.** Let `B` be a finite, self-enforcing annulus with finite
interior `I`. Assume `B` seals `I`: while `B` is present, the next contents of
`I` depend only on the current contents of `I`, every predecessor of a
configuration containing `B` also contains `B` at the same coordinates, and
the resulting finite transitions are realized with one fixed exterior
completion (zero outside the stable kynnös ring). Then there is a computable
map `F : {0,1}^I -> {0,1}^I`, and

```text
B with interior s is in Life's limit-set language
iff s lies on a directed cycle of F.
```

*Proof.* The sealing condition defines `F`. If `s` is on a cycle, repeating
the cycle gives predecessors of every depth. Conversely, arbitrary-depth
predecessors give paths of unbounded length ending at `s` in the finite
functional graph of `F`. An arbitrarily long path repeats a state. Its
repeated segment is a directed cycle, and determinism prevents a path from
leaving that cycle, so the endpoint `s` is on it. Cycle membership is
decidable by iterating at most `2^|I|` states. This is also the argument used
for the kynnös rings in the 2022 paper.

**Consequence.** No effective reduction from `NONHALT` can map `(M,w)` only to
a fixed self-enforcing kynnös ring with a finite interior computation. For
each constructed instance, cycle membership can be decided by finite
enumeration, which would decide `NONHALT`. Enlarging the ring as a computable
function of `(M,w)` changes the running time but not this decidability
obstruction.

Thus the feature that made the PSPACE reduction work is exactly what blocks
this proposed upgrade: a fixed ring turns arbitrary-depth ancestry into
recurrence in a finite state space. PSPACE machines use bounded tape and can
be arranged to return to their initial state on acceptance. A nonhalting
machine requires genuinely unbounded tape or another unbounded state
reservoir, which a fixed finite interior cannot provide.

## Sufficient expanding-cone lemma

A `Pi^0_1`-hardness proof would close if the following concrete Life gadget
family were constructed. For every deterministic machine `M` and input `w`,
it must effectively provide a finite cap `C(M,w)`, nested finite regions
`D_0 subset D_1 subset ...`, and encoded patterns `E_t` on `D_t` satisfying:

1. **Finite seed:** `E_0 = C(M,w)` encodes the initial machine state, head and
   finite input. The output pattern makes no assumptions outside `D_0`.
2. **Universal inverse soundness:** for every full-plane `x` and every `t`,
   `g(x)` containing `E_t` implies that `x` contains `E_(t+1)`. This quantifies
   over exterior debris, phases and all noncanonical Life preimages.
3. **Growth and sealing:** `D_(t+1)` contains enough newly forced cells to
   represent every tape cell first visited at machine time `t+1`; no signal
   entering from outside `D_(t+1)` can change the decoded transition.
4. **Full-plane completeness:** if `M(w)` has not halted by time `t+1`, every
   forced finite inverse step `E_(t+1) -> E_t` extends to a full-plane Life
   predecessor, compatibly for every finite depth.
5. **Halting kill:** if the encoded state at time `t` is halting, `E_t` has no
   encoded next predecessor; by soundness it has no predecessor at all.
6. **Effective uniformity:** the finite cap and local encoding data are
   computable from `(M,w)` (with polynomial cap size for a polynomial
   many-one reduction).

Under these six obligations, induction gives

```text
C(M,w) has an n-step predecessor iff M(w) runs for at least n steps,
```

so compactness gives `C(M,w)` in the limit-set language iff `M(w)` does not
halt. This is the complete reduction skeleton; the missing Life lemma is
obligations 2--4, not the computability argument.

The published components satisfy only strict fragments:

- kynnös gives stationary sealing, hence the finite-trap lemma rather than
  growth;
- marching band gives inverse-time boundary motion for an already infinite
  half-plane, not a boundary forced from a finite cap;
- backward circuits give universal soundness for one inverse step, but not
  temporal closure or second-preimage control.

This identifies the useful finite search target: a **cap transition**, meaning
a finite output patch that forces both a shifted/expanded boundary segment and
a canonical interior encoding in every predecessor while admitting at least
one such predecessor. The next section reports such a transition and states
the remaining failure that prevents iteration.

## Finite cap-transition search

`cap_search.py` carries out that search for the published marching-band motif
and finds a genuine, but non-iterable, cap transition. Write `R` for the
`8 x 4` marching band and extend it periodically. For integer `p`, the exact
candidate predicate is:

- constrain the Life output rectangle
  `[0,2p+7] x [0,2p+3]` to phase `(0,0)` of `R`;
- leave every other output cell unconstrained;
- quantify over every assignment to the complete radius-two predecessor
  rectangle `[-2,2p+9] x [-2,2p+5]`;
- require every two-step predecessor to equal `R` on
  `[10,2p-11] x [-1,2p+4]`;
- separately require that at least one two-step predecessor exists.

For `p=15`, the `38 x 34` output rectangle is satisfiable and forces all 360
cells of the `10 x 36` rectangle `[10,19] x [-1,34]` in every two-step
predecessor. In particular, it forces the full canonical `10 x 34` interior
strip and one new matching marching-band row beyond each horizontal output
edge. This improves the `p=20`, `48 x 44` sufficient witness stated as Lemma
22 in the 2022 paper for this narrower forced-strip predicate.

The immediately smaller candidate `p=14` is completely excluded for this
exact phase and predicate: the CNF is satisfiable both with the canonical
predecessor and with predecessor cell `(10,-1)` flipped. Thus its first
required expanded-row bit is not forced. No claim is made about other phases,
nonrectangular targets, or a different forced region.

This is not yet the expanding simulation cone of the sufficient lemma. In two
inverse Life steps the verified transition gains one row at the top and
bottom but loses 14 columns on each side (`38 -> 10`). It therefore cannot be
iterated at a fixed positive width, and it does not make a closed cap or force
the predecessor strip to contain the backward-circuit output type. A usable
reduction needs corner/side gadgets whose combined inverse transition has
nondecreasing transverse width and temporal type closure.

The SAT encoding is direct. The first Life step uses the 512-clause truth
table relation for each intermediate cell; the second step excludes every
neighborhood assignment inconsistent with the fixed output bit. No
periodicity is imposed on SAT variables. The successful instance has 3,036
variables and 1,034,392 clauses. Each forced-cell claim is a separate UNSAT
query obtained by assuming the opposite bit. `cap_result.json` records the
bounded search, and `--emit-query` writes any individual claim as DIMACS with
a SHA-256 digest for an independent solver. For the expanded-row query
`p=15`, cell `(10,-1)`, the emitted 1,034,393-clause DIMACS has SHA-256
`7929759778f94de721dd9334184a9b9aa072897c18a38eecd7f55731810ccca4`;
both CaDiCaL 1.9.5 and Glucose 4.2 return UNSAT.

## Exact transverse obstruction

The target-shape branch of the search did not find a noncontracting,
type-closed transition. It did produce an exact bounded obstruction that
rules out all target-shape weakening inside the successful rectangle, rather
than just one proposed shape.

Fix phase `(0,0)`, constrain the full `38 x 34` output rectangle as above, and
consider the complete available predecessor row

```text
[-2,39] x {17}.
```

The matching marching-band value is forced exactly at

```text
[1,28] x {17}  union  {(31,17)}.
```

It is not forced at any of the other thirteen positions. Thus the longest
contiguous canonical interval on this central row has width 28. In particular
no width-38 interval in the complete radius-two predecessor domain is forced.
This improves the previously recorded guaranteed interior width from 10 to
28, but it is still a strict `38 -> 28` contraction and cannot be the requested
type-closed transition.

Here “exact” has a finite, checkable meaning. `slice_forcing.cnf.gz` is the
direct two-step Life CNF plus one clause saying that at least one cell differs
among the 29 forced slice positions or the 360 positions in the cap-transition
claim above. The uncompressed formula has 3,036 variables and 1,034,393
clauses. It was exported, parsed back from DIMACS, and checked UNSAT by Glucose
4.2; the search itself used CaDiCaL 1.9.5. Thus both marching-band universal
forcing claims are covered by the exported aggregate query. For each of the
thirteen remaining positions, `slice_result.json` contains a complete
assignment to the `42 x 38` predecessor and `40 x 36` intermediate
rectangles. `cap_search.py` evaluates Life directly on every represented
neighborhood and checks both steps, including the requested flipped bit.
The uncompressed DIMACS SHA-256 is
`666f77cfd2b3f5d2f6a09291048046b4daf09fa6ed45ed692b8b681da042f763`;
the checked-in gzip SHA-256 is
`96122ff9130769aed31ff9d6499ad8361dfa9d1f43a5d6e96c99992669253ae8`.

There is also a useful maximality consequence. Let `A` be this marching-band
phase and let `D=[0,37] x [0,33]`. Among all output patterns obtained by
fixing an arbitrary subset of cells in `D` to their values in `A`, the full
pattern `A|D` has the strongest predecessor constraints: every predecessor of
`A|D` is a predecessor of any such partial pattern. Therefore each replayed
countermodel above is also a countermodel for every target obtained by
deleting cells or changing the target shape within `D`. No alternative
phase-`(0,0)` target shape contained in this bounding box and retaining the
canonical marching-band predecessor can force a noncontracting canonical
row. This monotonicity statement is exact and unbounded over the collection
of subsets of `D`; its SAT input is only the stated finite box.

The obstruction does **not** cover a larger bounding box, values inconsistent
with the canonical agar but admitting another composable predecessor type,
other phases, off-agar side or corner gadgets, longer inverse time, or a
finite alphabet of types. In particular it is not a no-go theorem for an
expanding cone and does not improve the PSPACE-hardness result to
`Pi^0_1`-hardness.

## Sources for this obstruction

- V. Salo and I. Törmä, *What Can Oracles Teach Us About the Ultimate Fate of
  Life?*, ICALP 2022, Lemma 21 and the paragraph following Figure 5 (fixed
  kynnös rings reduce limit-set membership to periodic evolution of the
  finite interior), and the proof of Theorem 2 (bounded-space PSPACE
  simulation).
- V. Salo and I. Törmä, *Structure and computability of preimages in the Game
  of Life*, Theoretical Computer Science 1024 (2025), Sections 7 and 10
  (semiweak one-step universality; strong universality and long-term backward
  computation remain open, with second-order preimages uncontrolled),
  DOI `10.1016/j.tcs.2025.115237`.
