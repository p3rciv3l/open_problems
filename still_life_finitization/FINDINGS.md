# Scoped findings: still-life finitization

## Complete period-3 all-window theorem

Let `P` be any Conway Life still life invariant under translations by `(3,0)`
and `(0,3)`. Every nonempty finite axis-aligned rectangular window cut from
`P`, at every origin and of every positive width and height, has a finite
still-life extension with dead-exterior margin at most 4.

This is a complete theorem for the class, not a bounded-margin search. It
includes 126 nonempty dense agars, including agars with interacting infinite
live components, and therefore goes beyond both the separated-component
family and the alternating-row family.

### Exhaustive host classification

In a 3x3-periodic configuration, the eight neighbors of a cell occupy each of
the other eight residue classes exactly once. If the tile has `K` live
residues, a live cell has `K-1` live neighbors and a dead cell has `K`. The
still-life rule therefore leaves exactly the empty tile and the
`binomial(9,4) = 126` tiles with four live residues. Thus every listed host is
globally stable on the whole plane; periodic stability is not inferred from a
finite window. The empty host has the empty finite extension and needs no SAT
seed.

The independent classifier also enumerates all 512 bit tiles and obtains
exactly the same 127 tiles. Translation and the eight square symmetries reduce
the 126 nonempty tiles to five orbits, represented by

```
11.  11.  11.  11.  1..
1..  11.  1..  1..  1..
1..  ...  .1.  ..1  .11
```

Square symmetries preserve the Life rule, finite support, Chebyshev margin,
and axis-aligned rectangles, so these five representatives cover every host.

### Finite-state pumping certificate

For each of the five representatives, nine window-origin phases, and all
width/height pairs in `1..15`, SAT finds a finite still life in margin 4.
There are 10,125 seeds. A dimension below 10 is a finite base case. A
dimension at least 10 uses one of the six bases `10..15`, selected by its
residue modulo 6.

Every pumpable seed additionally equates the two columns immediately before
a six-column block with the two columns immediately before its far seam. The
analogous equalities hold for row pumps. These pairs are the complete
radius-1 transfer boundary state. Duplicating the six-column or six-row block
therefore creates only local three-column or three-row neighborhoods already
present in the checked seed. Six is two host periods, so duplication preserves
the fixed core. Horizontal and vertical pumps commute.

For arbitrary width `w >= 10`, choose the unique base in `10..15` congruent
to `w` modulo 6 and repeat the horizontal pump. Do the same independently for
height. This proves coverage of every positive dimension, rather than
extrapolating from 15. `automata/period3_certificate.json` stores every seed
as a bounded bitmap, a digest of the ordered seed list, and an aggregate
digest of all 10,125 deterministic CNFs. The independent verifier exhaustively
rechecks the host classification, orbit coverage, every finite still life,
all seam states, one-step pumps, combined pumps, commutation, seed coverage,
and the seed digest without calling SAT. The checked certificate SHA-256 is
`8233abbabae6ffcafb657466d9f306e4faa3613b58e52571f271370b9568dcda`.

### Counterexample search direction and exact limit

The same exhaustive classification is also a counterexample search over every
3x3 periodic candidate host. No non-finitizable window exists in this class,
by the pumping theorem. Finite searches on the first dense representative
gave first-SAT margins 1, 2, 3, and 3 for aligned square windows of sides 1,
3, 6, and 9. The preceding UNSAT solver results have no retained proof traces;
they motivated the boundary-state search but are not used in the theorem or
to claim non-finitizability. Each sequence terminates in a directly checked
finite witness.

The theorem does not settle periodic hosts whose horizontal or vertical period
does not divide 3, general sofic hosts, or arbitrary infinite still lifes. No
finite-margin UNSAT result is presented as a counterexample, and no general
compactness principle follows from this class-specific transfer automaton.

## Alternating-row all-window theorem

Let `R_e` have every cell in even-numbered rows live and every cell in
odd-numbered rows dead; let `R_o` be its one-row translate. Every finite
nonempty rectangular window cut from either pattern has a finite still-life
extension with dead-exterior margin at most 3. The result holds for every
origin, width, and height. By rotation, it also holds for both phases of the
patterns with alternating entirely-live and entirely-dead columns.

These agars are not separated finite-component arrays: each live row or column
is an infinite live component. The theorem therefore lies outside the
component-agar lemma below.

### Pump construction

The exact certificate partitions dimensions at thresholds 9:

| Seed class | Widths | Heights | Phases | Count |
|---|---:|---:|---:|---:|
| finite | 1..8 | 1..8 | 2 | 128 |
| horizontal pump | 9..11 | 1..8 | 2 | 48 |
| vertical pump | 1..8 | 9..12 | 2 | 64 |
| two-dimensional pump | 9..11 | 9..12 | 2 | 24 |

There are 264 seeds in total. Every seed is a finite still life agreeing with
its core and dead outside margin 3. A horizontal pump duplicates a 3-column
block. Its two columns of left context equal the two columns at the wrap seam.
A vertical pump similarly duplicates a 4-row block with two matching context
rows. Conway Life has radius 1, so every newly created local 3-column (or
3-row) neighborhood is identical to one already verified in the seed.
Horizontal insertion preserves the core because the agar is constant along a
row. Vertical insertion preserves it because four rows are two full periods.
The two insertions commute.

For arbitrary width `w >= 9`, choose the unique base width in `9..11`
congruent to `w` modulo 3 and pump `(w-base)/3` times. For arbitrary height
`h >= 9`, choose the unique base height in `9..12` congruent to `h` modulo 4
and pump `(h-base)/4` times. Dimensions below 9 select the corresponding
one-directional or finite seed. The two seed phases cover the window's top-row
parity; horizontal translation is immaterial because the pattern has period 1
in that direction. This covers every positive `(w,h)`, not a finite cutoff.

`automata/alternating_rows_certificate.json` retains every seed witness, its
CNF digest and solver counters, and a digest of the complete ordered seed list.
The independent verifier does not trust SAT for the upper bound: it directly
checks all 264 still lifes, seam equalities, one-step pumps, combined pumps,
commutation, coverage, and digests. Repeated pumping then follows from the
radius-1 seam argument. The checked certificate SHA-256 is
`2c604b60dbb8fdc8d66d844d4f406853e1711fc0175c74e3792b77f453d4ea6b`.

The previous SAT sequence for live-row height-1 windows begins
`1,1,2,2,3,...`, so margin 3 is attained in those solver results. The theorem
asserted here is the independently checkable uniform upper bound; the
certificate does not turn the UNSAT sides into proof traces.

## Separated-block all-window theorem

For integers `p,q >= 4`, let `A(p,q)` be the infinite Life pattern consisting
of a 2x2 block at every translate `(ip,jq)`, `i,j` integral. For **every**
nonempty axis-aligned rectangular window, at every origin and of every finite
width and height, its restriction from `A(p,q)` has a finite still-life
extension with uniform dead-exterior margin at most 1. This bound is sharp over
the family: a 1x1 window containing one live corner of a block is UNSAT at
margin 0 and SAT at margin 1.

The construction takes exactly those translated 2x2 blocks having at least one
live cell in the window and includes each such block in full. It agrees with
the window because it is a subset of the original agar and includes every
window-live cell. Each included cell is within Chebyshev distance 1 of an
intersecting window cell, giving margin 1. Distinct blocks have live-cell
Chebyshev separation at least 3 when `p,q >= 4`; consequently the radius-1
neighborhood of any cell meets at most one block. An arbitrary finite union of
the selected blocks is therefore a still life. Only finitely many blocks meet
a finite window.

This is an instance of a more general component-agar lemma implemented in
`still_life/transfer.py`: if a finite still-life motif has Chebyshev diameter
`D` and its lattice translates have pairwise live-cell separation at least 3,
then every rectangular window has a stabilization of margin at most `D`, by
completing every intersected motif copy.

### Finite-state transfer certificate

For the original `A(4,4)` agar, a rectangle is represented by
`(left phase, right phase, top phase, bottom phase)` modulo 4. There are 256
states. `E` advances the right phase and `S` advances the bottom phase, giving
512 transitions. Every rectangle starts at one of 16 one-cell states and is
reached by `E^(width-1) S^(height-1)`; the two transfers commute.

Windows differing by a full period add only complete, mutually isolated motif
copies, so the component lemma preserves the construction invariant. It is
therefore sufficient to check one canonical rectangle for every boundary-phase
state, together with the motif and separation lemmas.

`automata/block_4x4_certificate.json` records the deterministic analysis:
all 256 canonical states verify directly, the minimum copy separation is 3,
the transitions are closed and commuting, and the transition digest is
`2ffca6d4ea2f1c0e1a245ae944f59218e339e1601e8691fa5a25cc1043aa6c96`.
The certificate is independently recomputed in the test suite. This is an
all-window proof, not an extrapolation from a finite side-length cutoff.

## Scope

These experiments use the following finite problem only. A rectangular core is
fixed cell-for-cell from an infinite periodic Life still life. For margin `m`,
all cells outside the core expanded by `m` in each direction are required dead.
The question is whether the cells in the margin can make the whole finite
configuration a still life. This is not a result about arbitrary finite subsets,
other cellular automata, or margins measured non-uniformly.

`experiments/results.json` records 64 cases produced by
`experiments/run_experiments.py` using python-sat 1.9.dev7's `cadical195`
backend. It contains 123 solver calls: 59 UNSAT and 64 SAT. Each first SAT
witness passed the separate direct checker. The largest call had 256 variables
and 46,140 clauses. For each call the result retains the exact variable and
clause counts, solver counters, and a SHA-256 digest of the clause stream.

## Exact observations

The entries below give the proved minimum uniform margins. A value `m` means
that every margin below `m` was UNSAT and margin `m` was SAT.

| Family | Window parameter | Minimum margins |
|---|---|---|
| 4x4 block agar, origin (0,0), square | side 1..12 | `1,0,0,0,1,0,0,0,1,0,0,0` |
| 4x4 block agar, origin (1,1), square | side 1..12 | `1,1,1,1,1,1,1,1,1,1,1,1` |
| 5x5 tub agar, origin (0,0), square | side 1..12 | `0,1,0,0,0,2,1,0,0,0,2,1` |
| 5x5 tub agar, origin (2,2), square | side 1..12 | `0,0,0,0,1,2,2,2,2,2,2,2` |
| 5x5 tub agar, origin (0,0), height-1 strip | width 1..16 | `0,1,1,1,1,1,1,1,1,2,2,2,2,2,2,2` |

The block sequences reflect cuts through separated 2x2 blocks: period-aligned
cuts often already contain complete finite blocks, while the shifted phase
consistently needs one layer. The tub cases show a small growth pattern. In the
dead-phase square family the observed minimum rises from 0 to 1 to 2 and stays
at 2 through side 12. In the height-1 strip family it rises from 0 to 1 to 2
and stays at 2 through width 16. Aligned tub squares instead oscillate with the
tile phase.

The targeted search in `experiments/adversarial_results.json` adds 80 exact
cases and 216 solver calls (136 UNSAT and 80 SAT). Three larger isolated-motif
agars were cut at phases selected to expose the largest margins in an
exploratory phase sweep:

| Family and fixed origin | Side 1..16 minimum margins |
|---|---|
| 6x5 beehive agar, (5,4) | `0,0,1,1,0,0,1,2,1,1,0,1,1,2,1,1` |
| 6x6 loaf agar, (5,3) | `0,0,0,1,2,2,2,2,2,2,2,2,2,2,2,2` |
| 6x6 pond agar, (5,5) | `0,0,1,1,0,0,0,1,1,1,0,0,0,1,1,1` |

A denser agar with infinite live components was also tested before the pump
theorem above was constructed: alternating entirely-live and entirely-dead
rows. For live-row windows of height 1 and width 1..32, the exact minima are

`1,1,2,2,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3`.

This gives genuine finite growth from 1 to 3 in a non-component agar. The
finite plateau alone did not justify extrapolation; the separate pump
certificate above now proves the global upper bound of 3 for all rectangles.

## Interpretation limits

The SAT data establish only the listed finite minima. The apparent plateaus may be
periodic boundary effects, and the observed rises do not imply that margins are
unbounded. No extrapolation beyond the tested windows is justified. UNSAT
results are solver results tied to the recorded deterministic CNFs; this run
did not retain independently checkable UNSAT proof traces. SAT sides are
stronger operationally because every emitted model is independently checked
against the Life rule and the dead-exterior condition.

The all-window separated-component theorem is different: it follows from the
explicit completion and finite-state/component invariants above, so it is not
limited by the experimental cutoff. It does not settle agars with interacting
or infinite live components.

The alternating-row theorem settles this one interacting, infinite-component
family only. It does not imply a bound for arbitrary periodic still lifes.
