# Still-life finitization

This directory studies one precise finite question. Given a rectangular window cut
from a spatially periodic Conway Life still life, it fixes every live and dead
cell in that window and asks for a finite still life contained in the rectangle
obtained by adding a uniform margin. Cells outside that rectangle are dead.

The SAT encoding has one variable per cell in the expanded rectangle. It
truth-table encodes the Life fixed-point rule at every cell in the rectangle and
its one-cell exterior halo. Core cells are fixed by unit clauses. Margins are
tested in increasing order, so a first SAT result after margins `0,...,m-1` are
UNSAT proves the minimum is `m` relative to this definition.

Install and run:

```sh
python -m pip install -r still_life_finitization/requirements.txt
python -m still_life_finitization.still_life.cli enumerate \
  --tile still_life_finitization/patterns/block_4x4.txt \
  --size 8 8 --max-margin 6 --output result.json
python -m still_life_finitization.still_life.cli verify result.json
python -m unittest discover -s still_life_finitization/tests -v
```

Reproduce the checked experiment result from the repository root:

```sh
python -m still_life_finitization.experiments.run_experiments
python -m still_life_finitization.experiments.run_adversarial
python -m still_life_finitization.automata.generate_certificate
python -m still_life_finitization.automata.generate_stripe_certificate
python -m still_life_finitization.automata.verify_stripe_certificate
python -m still_life_finitization.automata.generate_period3_certificate --jobs 3
python -m still_life_finitization.automata.verify_period3_certificate
python -m still_life_finitization.automata.generate_period4_certificate --jobs 4
python -m still_life_finitization.automata.verify_period4_certificate
```

`automata/block_4x4_certificate.json` is a deterministic finite-state transfer
certificate for the separated-block theorem. Its 256 states record the four
window-boundary phases modulo 4; its 512 `E`/`S` transitions cover extension by
one column or row. The analyzer checks transition closure and commutation,
every canonical phase state, the finite-component still-life condition, and
the separation lemma. `verify_transfer_certificate` independently recomputes
the full certificate.

More generally, `ComponentAgar` proves a constructive bound for any periodic
array of finite still-life motifs whose distinct copies have Chebyshev
separation at least 3: complete every motif that intersects the core. The
uniform margin is at most the motif's Chebyshev diameter.

`automata/alternating_rows_certificate.json` proves the separate all-window
theorem for the non-component agar with every other row entirely live. It
contains 264 directly verified finite seeds. Horizontal transfer inserts a
3-column pump, vertical transfer inserts a 4-row pump, and the two pumps
commute. The seed partition covers both vertical phases and every positive
width and height, proving a uniform margin bound of 3.

`automata/period3_certificate.json` proves an all-window theorem for every
Life still life invariant under translations by `(3,0)` and `(0,3)`. Direct
classification reduces all 512 tiles to the empty tile and 126 four-live-cell
tiles in five dihedral/translation orbits. The certificate contains 10,125
directly checked finite seeds for all representatives, phases, and pump
residue classes. Six-column and six-row transfers cover every larger
rectangle, with a uniform margin bound of 4. Its verifier uses only the Life
rule and certificate bitmaps; it does not invoke SAT.

`automata/period4_certificate.json` extends this to every still life having
some horizontal period and some vertical period at most 4. Exhaustive
classification of all 74,954 rectangular tiles gives 251 distinct hosts on a
common 12x12 lift and 13 translation/dihedral orbits. Earlier theorems cover
eight orbits (including the empty host); 19,176 checked seeds cover the five
new orbits. Radius-1 boundary states permit insertion of two full host periods
in either direction, proving the same uniform margin bound of 4 for all window
sizes. Verification enumerates the host class and directly checks every seed,
seam, pump, and commuting two-dimensional transfer without invoking SAT.

`still_life/periodic_transfer.py` states the same transfer argument without a
period cutoff.  For an arbitrary `p`-by-`q` periodic still life, a finite table
of directly checkable seeds is sufficient when its horizontal and vertical
pump lengths are multiples of `p` and `q`.  The table covers all origin phases,
all dimensions below the two pump thresholds, and one complete pump-residue
interval above each threshold.  Equality of the two full columns (respectively
rows) before each seam is the complete radius-1 boundary state.  The generic
verifier checks the host, arithmetic side conditions, table coverage, finite
still-life condition, and every seam; `construct_from_seeds` then handles every
positive window size.

This is a certificate theorem, not a proof that such a table exists for every
periodic host.  That existence claim is the still-life finitization problem and
remains open.  In particular, failure of a bounded-margin SAT search or of this
rectangular pump ansatz is not an all-margin obstruction.

Result files retain every tested SAT/UNSAT status, variable and clause counts,
solver statistics, and a SHA-256 digest of the deterministic clause stream.
SAT witnesses are checked by a separate direct Life implementation before being
emitted; the `verify` command reruns that checker without constructing a CNF.

Tile files use `1` for live and `.` for dead. Coordinates and the optional
window origin are in the infinite periodic tiling. Input tiles are rejected
unless direct toroidal checking confirms that they are periodic still lifes.
