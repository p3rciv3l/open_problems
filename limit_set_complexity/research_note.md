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

No new Life gadget is claimed here, so there is no new SAT gadget result to
report. A useful next finite search must target a **cap transition**: a finite
output patch that forces both a shifted/expanded boundary segment and a
canonical interior encoding in every predecessor, while admitting at least
one such predecessor. Another table showing that a stationary agar forces
itself cannot address the obstruction.

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
