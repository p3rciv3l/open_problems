# Periodic Conway Life density optimizer

This package exactly maximizes total live cells across `P` phases of B3/S23
Life on a `W x H` torus under Z3 solver trust. It uses Z3 constraints for every
transition and incremental bounded optimization. `--exact-period` excludes
every proper divisor of `P`. Each JSON witness is independently re-simulated by
code that does not use Z3.

Wrapped Moore-neighborhood **directions** are counted, so all eight offsets
contribute even when coordinates coincide on tori narrower than three cells.

```bash
python -m pip install -e .
life-density optimize 5 5 2 --exact-period -o witness.json
life-density verify witness.json
life-density grid --widths 3,4 --heights 3,4 --periods 1,2 -o results.json
python -m unittest discover -s tests
```

Output uses schema `life-density/v1`, represents dead/live cells as `.`/`O`,
stores density as an exact numerator and denominator, and records solver
version, seed, search bounds, and independent witness verification. Optimality
is solver-certified from bounded SAT/UNSAT queries; no independently checkable
UNSAT proof artifact is emitted, so the optimality claim is not independently
certified. A timeout returns status `unknown` rather than claiming an optimum.

Reproducible sample output is checked in at `results/small_grid.json`; regenerate
it with:

```bash
life-density grid --widths 3,4 --heights 3,4 --periods 1,2 \
  --exact-period -o results/small_grid.json
```
