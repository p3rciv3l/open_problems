# Life limit-set complexity: finite forcing experiment

This directory addresses only the exact-complexity question for the language
of Conway's Life limit set. It does **not** prove a new hardness result. Its
computational contribution is a finite, reproducible subset of Salo and
Törmä's köynnös forcing calculation.

## Reproduced claim

Let `P` be the `6 x 3` tile

```text
111000
010111
000010
```

and extend it periodically. For each of the 18 spatial phases, constrain a
`30 x 27` Life output rectangle to the corresponding part of this agar.
Among all assignments to its `32 x 29` one-step predecessor rectangle, the
matching central `6 x 3` tile (`x=12..17`, `y=12..14`) is forced.

This is deliberately smaller than Lemma 17 of Salo--Törmä, which reports a
larger common forced rectangle from the same `30 x 27` experiment. The
calculation here makes 324 UNSAT queries (18 cells in each of 18 phases), plus
one satisfiability query per phase. It says nothing about output rectangles
smaller than `30 x 27`, arbitrary cells outside the queried tile, multiple
time steps, or computational hardness.

## Run

```bash
python -m venv .venv
.venv/bin/pip install -r requirements.txt
./run_checks.sh
```

`run_checks.sh` first checks the encoder against all 512 local assignments,
checks the agar directly under the Life rule, and verifies one complete
forcing phase. It then verifies all köynnös phases, runs the bounded
marching-band cap search, and writes both result files. The two full SAT
computations are intentionally much slower than the unit tests.

Each target cell is encoded directly: every one of the 512 neighborhood
assignments producing the wrong output contributes the clause excluding that
assignment. There are no auxiliary variables or imported Life encoders.

For an independently consumable DIMACS instance, append the unit clause that
contradicts one claimed forced value:

```bash
python forcing.py --emit-cnf query.cnf --phase 0,0 --cell 12,12
kissat query.cnf  # or another DIMACS-compatible SAT solver; expected UNSAT
```

The command prints the SHA-256 digest of the emitted file. Coordinates,
variable numbering, local rule, clause generation, and the expected agar are
all in `forcing.py`.

The cap search and one independently checkable boundary query are:

```bash
python cap_search.py --min-padding 14 --max-padding 20 --output cap_result.json
python cap_search.py --emit-query query.cnf --padding 15 --cell 10,-1
```

## Files

- `forcing.py`: direct CNF encoder, PySAT verifier, and DIMACS exporter.
- `cap_search.py`: two-step marching-band cap-transition search and DIMACS
  exporter.
- `tests/test_forcing.py`: exhaustive local-encoding and finite-witness tests.
- `result.json`: generated results for all 18 phases.
- `cap_result.json`: generated bounded cap search, including the verified
  `38 x 34` transition and the excluded `36 x 32` candidate.
- `research_note.md`: exact logical scope, a complete conditional reduction
  skeleton, and the fixed-ring finite-state obstruction.

## Sources

- V. Salo and I. Törmä, *What Can Oracles Teach Us About the Ultimate Fate
  of Life?*, ICALP 2022, DOI
  [10.4230/LIPIcs.ICALP.2022.131](https://doi.org/10.4230/LIPIcs.ICALP.2022.131).
  See Theorem 2, Lemma 17, and the discussion of köynnös.
- Their accompanying
  [`gol-agars`](https://github.com/ilkka-torma/gol-agars) repository,
  especially `verify_agars.py`. This implementation uses the published tile
  and dimensions but is otherwise a fresh, minimal encoder.
