# Strong Unique Father: finite forcing checks

This directory implements a deliberately finite claim based on Törmä and
Salo's [`gol-agars`](https://github.com/ilkka-torma/gol-agars) method.  A SAT
instance contains every cell in the one-cell halo of a specified finite image
patch and the exact B3/S23 local rule.  A cell is reported as forced only when
the instance with its opposite value is UNSAT.  A non-forced cell is accompanied
by the complete halo assignment of a counter-predecessor.

The included baseline witness is the published 32 by 26 population-334
stabilization of the 6 by 6 `kynnös` self-forcing agar.  The stronger search
candidate repeats two additional agar periods in each direction, giving a
44 by 38 population-710 still life.  With two complete dead-output rings
constrained around it, 646 of 710 live cells and 1478 of 1580 convex-hull
assignments are forced.  The corresponding baseline figures are 286 of 334
and 662 of 740.

The checks at dead-output annulus widths 0, 1, and 2 give the same figures for
both witnesses.  Expanding annuli are important asymmetrically: an UNSAT result
at any finite width proves forcing against arbitrary global predecessors, but
a finite SAT countermodel need not extend to a global predecessor.  The report
therefore emits those models without claiming that the remaining cells are
globally non-forced.

Run:

```sh
python -m pip install -e '.[test]'
python -m strong_unique_father.cli --annulus 2 --output report.json
python -m pytest
```

The report gives separate metrics for live cells and every live/dead lattice
assignment in the geometric convex hull.  It also records exact models for
every unforced requested cell.  `--independent` rechecks every forced literal
with a second, truth-table CNF encoding and a different SAT backend, and
directly evolves every counter-predecessor.

This is a stronger reproducible finite backward-forcing result, not a solution
of the strong Unique Father problem.  In particular, 64 live cells remain
unforced by the width-2 finite check, and their countermodels are not claimed
to be globally extendable.
