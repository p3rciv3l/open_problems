# First exploration: density and random initial conditions

The first computational pass produced three complementary artifacts. It did
not solve an open problem, but it established a reproducible baseline with a
clear distinction between exact bounded results, exact local proofs, and
finite empirical measurements.

## Exact finite-torus optimization

The `life_density` solver encodes every B3/S23 transition across a prescribed
spatial torus and temporal period in Z3. It can require the least temporal
period to equal the requested period, maximizes total spacetime population by
integer binary search, and emits every phase. A separate pure-Python verifier
checks the witness without Z3.

The initial grid contains all width-height pairs in `{3, 4}` and periods 1 and
2. Seven instances are feasible. Every feasible optimum has average density
at most `1/2`; six attain `1/2`, while the exact `3 x 3` still-life optimum is
`4/9`. There is no exact-period-2 orbit on the directional-Moore `3 x 3`
torus.

These are exact results under Z3 solver trust for the stated finite
instances. The witnesses are independently checked, but the upper-bound half
does not yet have a standalone UNSAT proof artifact. The instances are also
far too small to imply the infinite `1/2` conjecture.

## Exact local inequality

The `life_agar_certificate` experiment searches the following radius-one
telescoping inequality over all 512 input neighborhoods:

```text
current center <= bound
                  + horizontal face potential difference
                  + vertical face potential difference
                  + temporal cell potential difference.
```

It finds `bound = 8/13`. The stored rational certificate verifies every local
case exactly. Summing translated copies over any finite spatial and temporal
torus cancels every potential, proving average density at most `8/13`.

A rational distribution supported on 57 neighborhoods satisfies every dual
face-balance equation and has center occupancy `8/13`. It proves that no
better bound is possible within this precise radius-one, one-step potential
family. The distribution is only locally consistent and need not extend to a
Life spacetime.

This reproduces the classical `8/13` bound in a compact machine-checkable
form; it does not improve the current `1176/2087` bound and does not prove
`1/2`. Its main value is architectural: future, larger potential families can
reuse the dependency-free exact verifier and must beat an exactly established
baseline.

## Finite random baseline

The `life_experiments` harness ran 12 seeded trials for each combination

```text
initial p = 0.1, 0.3, 0.5, 0.7
torus side L = 32, 64, 128
generations = 200
```

At generation 200, mean live densities over the 12 trials ranged from
`0.03271` to `0.07634`. For `L = 128`, the means were:

| Initial density | Live density at generation 200 | 95% normal interval |
|---:|---:|---:|
| 0.1 | 0.04654 | [0.04102, 0.05206] |
| 0.3 | 0.07160 | [0.06515, 0.07805] |
| 0.5 | 0.07634 | [0.07118, 0.08150] |
| 0.7 | 0.04239 | [0.03818, 0.04661] |

No `128 x 128` trial repeated a complete torus state within 200 generations.
Smaller tori repeated more often, reaching 75% of trials for `p = 0.7`,
`L = 32`. This is a visible finite-size effect, not evidence about
stabilization on the infinite plane. The full time series, seeds, activity
rates, period detections, and run metadata are stored in JSON and CSV.

## Next proof search

The next density milestone is to beat `8/13` with an exact certificate, then
reproduce the published `1176/2087` bound in the same independently checked
format. The promising extension is a hierarchy of larger spatial face states
and deeper temporal windows:

1. Generate local spacetime blocks lazily rather than materializing every
   Boolean assignment.
2. Solve the floating-point primal and dual by column generation.
3. Rationalize only the sparse candidate dual.
4. Exhaustively separate violated local inequalities with SAT.
5. Emit a rational certificate plus a proof-producing SAT artifact for the
   separation step.

That path can turn additional compute into a stronger theorem. Enlarging the
finite-torus table alone cannot.
