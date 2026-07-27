# Strong Unique Father: finite forcing checks

This directory implements a deliberately finite claim based on Törmä and
Salo's [`gol-agars`](https://github.com/ilkka-torma/gol-agars) method.  A SAT
instance contains every cell in the one-cell halo of a specified finite image
patch and the exact B3/S23 local rule.  A cell is reported as forced only when
the instance with its opposite value is UNSAT.  A non-forced cell is accompanied
by the complete halo assignment of a counter-predecessor.

The included witness is the published 32 by 26 population-334 stabilization of
the 6 by 6 `kynnös` self-forcing agar.  The check intentionally constrains only
the stabilization's bounding rectangle.  This is an over-approximation of
predecessors of the entire finite still life, so forced-cell conclusions are
sound for arbitrary global predecessors; failure to force a cell is only a
finite-patch counterexample, not necessarily a global counterexample.

Run:

```sh
python -m pip install -e '.[test]'
python -m strong_unique_father.cli --output report.json
python -m pytest
```

The report gives separate metrics for live cells and every live/dead lattice
assignment in the geometric convex hull.  It also records exact models for
every unforced requested cell.  `--independent` rechecks every forced literal
with a second, truth-table CNF encoding and a different SAT backend, and
directly evolves every counter-predecessor.

This is a reproducible finite backward-forcing result, not a solution of the
strong Unique Father problem: no claim is made about uniqueness outside the
reported finite domains.
