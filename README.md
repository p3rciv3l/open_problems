# Conway Life finite-torus experiments

This repository contains a deterministic, NumPy-vectorized experiment harness
for Conway's Game of Life initialized from Bernoulli random fields on finite
periodic square tori.

**All generated results are empirical and finite-size. They concern finite
tori and finite run lengths and do not imply asymptotic theorems.**

The harness records live-cell density, per-generation activity (the fraction
of cells that change), exact repeated-state period detection, and normal
confidence intervals across independent seeded trials. Each trial's seed is
derived deterministically from the master seed and configuration, so results
do not depend on sweep ordering.

```bash
python -m pip install -e '.[test]'
life-experiment --p 0.1,0.3,0.5,0.7 --sizes 32,64,128 \
  --steps 200 --trials 12 --sample-every 10 --seed 20260727 \
  --output results/life_sweep
pytest
```

The command writes a detailed JSON document and a tidy CSV time series. Period
and transient summaries include only trials whose repeat was observed within
the configured finite time horizon; detection fraction is reported separately.
