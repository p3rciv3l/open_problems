# Local Life agar certificate experiments

The strongest certificate here proves the new bound
`43578/78167 ≈ 0.557499` for every finite, spatially periodic Life orbit,
improving the published `1176/2087 ≈ 0.563488` bound. It does **not**
prove the conjectured `1/2` bound.

## Exact `6 x 8` strip-pyramid optimum

`pyramid_6x8.cert` assigns nonnegative integer weights to a `6 x 8`
slice at time `t`, its determined central `4 x 6` slice at `t+1`, and
the determined central `2 x 4` slice at `t+2`. Its weights sum to
312668. Exact max-plus row dynamic programming exhausts all `2^48`
initial slices and proves maximum live weight 174312. Translating the
weighted shape over a space-time torus therefore gives density

```
174312/312668 = 43578/78167.
```

The same certificate contains a 19-slice exact dual distribution. On
every reflection orbit of cell positions its expected live count is at
least `43578/78167` times that orbit's size. Consequently every
normalized nonnegative weighting on this fixed shape has some legal
slice with score at least `43578/78167`. Reflection-averaging shows this
for arbitrary positional weights, not just symmetric ones. The bound is
therefore the exact optimum of the full nonnegative positional-weight
family on this `6 x 8 -> 4 x 6 -> 2 x 4` shape.

This is a proved fixed-window obstruction above `1/2`; it does not
obstruct larger shapes, additional time layers, or signed telescoping
potentials. `pyramid_6x8_search.py` reproduces the primal and dual by
sparse LP column generation. `strip_pyramid_separator.cpp` performs
each separation exactly and returns a maximizing legal slice.
`pyramid_6x8_verify.cpp` independently checks the integer certificate,
all `2^48` initial slices, and every dual marginal using only the C++17
standard library.

## Three-generation `6 x 6` pyramid

`pyramid_6x6.cert` assigns nonnegative integer weights to a `6 x 6`
slice at time `t`, its determined central `4 x 4` slice at `t+1`, and
the determined central `2 x 2` slice at `t+2`. The weights sum to 8348.
Exact exhaustive row dynamic programming proves that every one of the
`2^36` initial slices has live weight at most 4704. Therefore translating
the weighted shape over every space-time position of a torus gives

```
8348 * live cells <= 4704 * all cells,
```

and density at most `4704/8348 = 1176/2087`. This is a finite weighted
spacetime inequality rather than an assertion about unenumerated
orbits.

`pyramid_search.py` reproduces the weights with a ten-variable
dihedral-symmetric LP. It starts with a sparse set of legal evolution
columns and uses CP-SAT maximization as a separation oracle. The
resulting certificate does not trust either floating-point LP output or
CP-SAT: `pyramid_verify.cpp` reads the integer certificate, reapplies
B3/S23, and computes the exact maximum by max-plus row DP using only the
C++17 standard library.

## Two-center spacetime-strip inequality

The larger block contains a `4 x 3` slice at time `t` and the two Life
outputs above its middle horizontal pair at time `t+1`. Its left and
right faces each contain a translated `3 x 3` input block plus one output
bit, so they are genuine two-time-slice faces. The top and bottom faces
are `4 x 2` input strips, and the temporal faces are the current and next
two-bit center pairs.

For every block `a`, the rational tables in `strip2_certificate.json`
satisfy

```
c1(a) + c2(a) <= 12001/10000
                   + X[L(a)] - X[R(a)]
                   + Y[T(a)] - Y[D(a)]
                   + Z[C(a)] - Z[N(a)].
```

Summing over a finite space-time torus cancels every potential against a
translated copy. Each cell occurs twice on the left, giving density at
most `12001/20000`. The exact verifier checks all 4096 inequalities.

This tested ansatz has 1024 arbitrary values on each horizontal
spacetime-face type, 256 on each vertical face type, and four on each
temporal-pair type. A four-pattern nonnegative balanced witness proves
that no bound below `3/5` is possible in this ansatz. The checked upper
certificate is `12001/20000`, obtained by rounding the numerical LP
potential to a `1/10000` grid and then recomputing the required constant
exactly. Thus the **verified** LP-optimum interval is
`[3/5, 12001/20000]`; no claim of exact attainment at `3/5` is made.

## Radius-one baseline

For a `3 x 3` neighborhood `a`, let `c(a)` be its center and let `n(a)` be
the next state of that center under B3/S23. The two-column left and right
faces are `L(a), R(a)`, and the two-row top and bottom faces are
`T(a), D(a)`. The stored rational tables satisfy, for every one of the 512
neighborhoods,

```
c(a) <= 8/13
        + X[L(a)] - X[R(a)]
        + Y[T(a)] - Y[D(a)]
        + Z[c(a)] - Z[n(a)].
```

Sum this inequality over all cells and all times of a finite space-time
torus. Each spatial face term cancels its translated neighbor, and each
time term cancels at the next time. Thus the average density is at most
`8/13`. This applies to oscillating agars represented by any finite
spatial fundamental domain and any finite temporal period.

The baseline ansatz is intentionally small: spatial radius 1, time depth 1, an
arbitrary rational potential on each six-bit spatial face, and an
arbitrary rational potential on the one-bit temporal face. `8/13` is the
exact optimum **of this LP ansatz**. The nonnegative 57-pattern
`optimality_witness` in `certificate.json` has balanced face marginals,
total mass 1, and center occupancy `8/13`, so it gives the matching LP
lower bound. It is only a locally consistent fractional distribution; no
claim is made that it extends to a Life orbit.

## Reproduce and verify

The local-face verifiers use Python's exact `fractions.Fraction`
arithmetic. The pyramid verifier uses exact integers and the C++17
standard library:

```sh
cd life_agar_certificate
python verify.py
python strip2_verify.py
g++ -O3 -std=c++17 pyramid_verify.cpp -o pyramid_verify
./pyramid_verify pyramid_6x6.cert
g++ -O3 -std=c++17 pyramid_6x8_verify.cpp -o pyramid_6x8_verify
./pyramid_6x8_verify pyramid_6x8.cert
python -m unittest discover -s tests -v
```

To rerun the floating-point LP, rationalize its output, and check the
result exactly:

```sh
python -m pip install -r requirements.txt
python solve.py
python strip2_solve.py
python pyramid_search.py
python pyramid_6x8_search.py
python verify.py
python strip2_verify.py
```

The search scripts enumerate or separate legal B3/S23 evolutions and use
SciPy/HiGHS; the pyramid search additionally uses OR-Tools CP-SAT.
Floating-point and solver results are treated only as certificate
discovery. The stored outputs are accepted only by the exact,
solver-independent verifiers.
