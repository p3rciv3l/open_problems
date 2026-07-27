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

## Property still needed for a `Pi^0_1`-hardness reduction

A reduction from `NONHALT` would need a **finitely capped, adversary-proof,
unbounded backward simulation cone** with all of the following included in
the gadget statement:

1. A computable finite Life pattern `C(M,w)` marks a unique time-zero machine
   state, including a head and finite input.
2. Every depth-`n` predecessor of any completion containing `C(M,w)` forces,
   in a protected region, the first `n` steps of the deterministic computation
   of `M(w)`. No alternative phase, exterior debris, incoming signal, or
   malformed encoding may provide a spurious predecessor chain.
3. The protected region expands under inverse Life dynamics with enough fresh
   space for an unbounded tape. Its boundary is itself forced from the finite
   cap; an assumed infinite agar half-plane is not allowed in the reduction's
   output pattern.
4. Completeness holds: if `M(w)` runs for at least `n` steps, the forced
   depth-`n` spacetime patch extends to a full-plane Life predecessor.
5. A halting state has no next encoded predecessor. Thus
   `C(M,w)` has predecessors of every finite depth iff `M(w)` never halts.
   The construction and the finite output pattern must have size computable
   (polynomial size for the usual many-one formulation) from `(M,w)`.

Items 2 and 3 are the additional property absent from the verified köynnös
gadget: **finite seeding plus growing, sealed backward forcing**, rather than
forcing an already infinite periodic background. Item 4 is equally necessary
to turn local soundness into an iff reduction. A full hardness proof would
have to give concrete Life patterns and prove all five clauses; universality
or self-enforcement alone does not supply them.

The marching-band agar in the same paper supplies one-way boundary motion,
and kynnös supplies finite self-enforcing patches and stable rings. Those are
suggestive components, but the cited work does not prove that they couple to
an unbounded, finitely seeded, sealed computation cone. Consequently they do
not by themselves yield `Pi^0_1`-hardness.
