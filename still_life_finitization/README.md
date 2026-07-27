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
```

Result files retain every tested SAT/UNSAT status, variable and clause counts,
solver statistics, and a SHA-256 digest of the deterministic clause stream.
SAT witnesses are checked by a separate direct Life implementation before being
emitted; the `verify` command reruns that checker without constructing a CNF.

Tile files use `1` for live and `.` for dead. Coordinates and the optional
window origin are in the infinite periodic tiling. Input tiles are rejected
unless direct toroidal checking confirms that they are periodic still lifes.
