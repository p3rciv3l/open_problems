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

## Parametric family and exact obstruction

Let `S(n)` be the stabilization obtained by inserting `n` additional 6-cell
kynnös periods in both directions.  Direct counting gives

```text
width = 32 + 6n
height = 26 + 6n
population = 16n² + 156n + 334
convex-hull lattice cells = 36n² + 348n + 740
```

The published finite self-forcing kynnös patch can be translated across the
periodic interior of `S(n)`.  These translates cover everything except a
constant-width boundary strip.  The uncovered population is therefore `O(n)`
while the population and hull have size `Theta(n²)`, proving that both forced
coverage ratios tend to 1.  SAT checks for `n = 0, 1, 2, 3` sharpen the observed
defects to `8n + 48` live cells and `12n + 78` hull assignments respectively.
Those linear equalities are reported as a checked pattern, not as a general
SAT theorem.

Nevertheless, no member of this family reaches 100% live-cell forcing.  For
every `n >= 0`, define

```text
D = {(6,0), (7,0), (8,0), (8,1), (9,-1), (9,0), (9,1)}
P(n) = live(S(n)) symmetric_difference D
```

Exact finite evolution gives `g(P(n)) = S(n)`, while `(8,0)` is live in `S(n)`
and dead in `P(n)`.  This is a globally extendable finite counter-predecessor,
not a relaxed finite-window model.  The proof is parametric: expansion only
inserts rows at 10 and columns at 12, whereas all changed cells and all outputs
they can affect lie strictly before those seams.  Thus the same finite local
calculation applies to every `n`.

As a boundary-replacement check, the published minimum-population 306-cell
stabilization was also analyzed.  It forces only 262/306 live cells and
612/756 hull assignments, and localized exact counter-predecessors exist at
each tested side.  It does not remove the boundary obstruction.

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
unforced by the width-2 finite check.  At least one of them now has the exact
global counter-predecessor above, proving that repeated expansion of this
stabilization cannot produce a strong witness.
