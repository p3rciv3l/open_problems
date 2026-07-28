# Local Life agar certificate experiments

The strongest certificate here proves the new bound
`138867/250001 ≈ 0.555466` for every finite, spatially periodic Life orbit,
improving the published `1176/2087 ≈ 0.563488` bound. It does **not**
prove the conjectured `1/2` bound.

## Convergent pyramid hierarchy

The finite certificates below are levels of a complete, rather than merely
heuristic, local hierarchy. Let `P_n` contain generations `0,...,n`, starting
from a `6n x 6n` square and deleting one boundary cell on every side at each
generation. Normalize arbitrary nonnegative positional weights on `P_n` to
sum to one, and let `h_n` be the least possible maximum weighted live count
over all initial slices. Then

```
lim(n -> infinity) h_n = rho,
```

where `rho` is the largest one-cell expectation among translation-invariant
probability measures on bi-infinite Life spacetime diagrams. In particular,
every spatially and temporally periodic orbit has density at most every
`h_n`. Thus this hierarchy converges to the sharp invariant-measure bound;
proving that its limit is `1/2` would prove the conjecture (and the statement
also isolates the possible obstruction: an aperiodic invariant measure above
`1/2`).

Here is a short proof. Let `u_n` be the maximum for uniform weights on `P_n`.
For any invariant measure, the expectation of every normalized positional
weighting is its density, so

```
rho <= h_n <= u_n.
```

The pyramids `P_n` are a Følner sequence in space-time: their volume is
Theta(`n^3`), while every fixed-width spatial or temporal boundary is
O(`n^2`). Translate a maximizing finite diagram to every root in `P_n` and
average the resulting point masses. Any weak limit is translation invariant,
and the proportion of roots at which any fixed Life constraint meets the
boundary tends to zero, so the limit is supported on bi-infinite Life
diagrams. Its one-cell expectation is any corresponding limit of `u_n`;
hence `limsup u_n <= rho`. Averaging restrictions to `P_n` under any
invariant measure gives the reverse inequality `u_n >= rho`, proving
`u_n -> rho` and squeezing `h_n -> rho`.

The translation argument does not assume that a torus is wider than the
certificate. For each fixed certificate position, translation of the origin
is a bijection of any spatial or temporal torus, even when positions wrap or
coincide. Consequently its weight is counted exactly once at every torus
cell. B3/S23 on the lifted finite patch agrees with the wrapped update, and
temporal cancellation uses only an actual temporal cycle.

### What the `6 x 8`--`6 x 12` optima say

The exact maximizing slices expose a boundary transient, not a repeatable
high-density phase. At heights 8 and 12 a `6 x H` rectangle with its four
corners deleted is a maximizer; at height 10 the full rectangle is a
maximizer. Their three layer populations are respectively

```
(44, 0, 0), (60, 0, 0), (68, 0, 0).
```

Thus all three die completely in one step. The verifier proves that their
scores are the stored maxima, so this observation is exact. The small
`6 x 8`--`6 x 12` numerical drift is therefore not evidence of a repeatable
high-density configuration.

The exact `6 x 8` dual is subtler. Its expected births and deaths agree at
both transitions:

```
t -> t+1:  births = deaths = 501584/78167
t+1 -> t+2: births = deaths = 179920/78167.
```

It therefore fakes temporal stationarity at the level of one-cell marginals.
It is nevertheless very far from spatially repeatable. Symmetrize its 19
slices under the two rectangle reflections. The total-variation distances
between the laws of opposite one-cell-overlap faces are

```
             horizontal       vertical
layer 0      73904/78167       63504/78167
layer 1      50108/78167       38258/78167
layer 2          0             11754/78167.
```

Opposite overlap laws must be equal for the restriction of any
translation-invariant spatial measure. In particular, the layer-0 horizontal
defect is greater than `0.945`; the fixed-window dual obstruction cannot be
tiled, made Markov across its seam, or converge unchanged to an invariant
Life spacetime. `pyramid_obstruction.py` derives these fractions directly from
the stored integer dual and checks the three maximizing extinction slices.

### Exact characterization of a remaining obstruction

The preceding defect gives a useful theorem of alternatives. For finite legal
Life-pyramid laws `nu_n`, call the overlap defect at radius `r` the largest
total-variation distance between the laws of two congruent radius-`r`
subwindows whose roots differ by one spatial or temporal unit. Then a
translation-invariant bi-infinite Life measure of density at least `c` exists
if and only if there are pyramids with inradius tending to infinity, expected
root occupancy at least `c-o(1)`, and every fixed-radius overlap defect tending
to zero.

The forward implication is restriction of the invariant measure. Conversely,
compactness of probability laws on finite binary windows gives a diagonal
weak limit of the rooted laws. Vanishing overlap defects makes that limit
invariant, and the Life equations hold in the limit because they are closed
local constraints. This also proves the equivalent projective formulation in
which all congruent subwindow marginals agree exactly.

Consequently, failure of the `1/2` theorem is not represented by the stored
dual or by any other isolated finite-window pseudodistribution. It requires a
projectively coherent family with density uniformly greater than `1/2`. By
ergodic decomposition it may be chosen ergodic; if no periodic counterexample
exists, almost every spacetime in that component is aperiodic.

There is a further necessary local charging condition. In such an invariant
measure let `p` be live intensity, `s` the intensity of live cells that
survive, and `b,d` the birth and death intensities. Stationarity gives
`b=d=p-s`. Survivors have at most three survivor neighbors, so Elkies's
maximum-degree-three theorem gives `s <= 1/2`. Hence every counterexample must
satisfy

```
b = d >= p - 1/2 > 0,
P(cell changes state) = 2b >= 2p - 1.
```

This isolates the only remaining mechanism: a spatially coherent,
positive-flux (and, absent a periodic counterexample, aperiodic) family whose
birth/death transport survives every scale. A proof of `1/2` can equivalently
discharge that flux into the Elkies survivor deficit `1/2-s`; the present
three-layer positional certificates do not, because their dual pays for it
with the quantified seams above.

### Exact obstruction to population-only temporal charging

Here is a precise limit of the survivor/birth/death approach. Let `A_t` be a
Life generation on an `N`-cell king-grid torus and put

```
S_t = A_t intersect A_(t+1),
B_t = A_(t+1) - A_t,
D_t = A_t - A_(t+1).
```

Then `|A_(t+1)|=|S_t|+|B_t|`, `|A_t|=|S_t|+|D_t|`, every birth has exactly
three neighbors in `S_t union D_t`, and every survivor has two or three such
neighbors. On a temporal cycle, `sum |B_t|=sum |D_t|`. These statements are
not enough for either of the two most direct charging lemmas.

First consider the affine one-step lemma

```
|S_t| + |B_t| - N/2 <= alpha (|B_t| - |D_t|).                 (A)
```

Any fixed `alpha` would prove the conjecture after summing around time. On the
`3 x 3` torus, however, one full live row evolves to the full torus and then
to the empty torus:

```
###    ###    ...
... -> ### -> ...
...    ###    ...
```

The first transition has `(S,B,D)=(3,6,0)`, so (A) requires
`9-9/2 <= 6 alpha`, or `alpha >= 3/4`. The second has
`(S,B,D)=(0,0,9)`, so it requires `-9/2 <= -9 alpha`, or
`alpha <= 1/2`. Thus no population-only linear temporal potential can close
the survivor deficit. The associated bipartite count is sharp: the six births
have all three predecessors among the three survivors, giving exactly 18
birth--survivor incidences; the survivor graph is a 3-cycle and has degree
two. The next transition consists of nine mutually overpopulated deaths.

Nor can an uncorrected fixed temporal window work. The proposed statement

```
sum_(i=0)^(k-1) |A_(t+i)| <= kN/2                              (W_k)
```

already fails for `k=2` in the `3 x 3` example, with `3+9>9`. This torus is
minimal among ordinary rectangular king tori, whose two dimensions must be at
least three to give eight distinct neighbor positions. Exact enumeration of
all 512 states shows that every `3 x 3` prefix of every length `k>=3` does
satisfy `(W_k)`. The next possible torus, `4 x 3`, has the sharper transient

```
###.    #.#.    #.#.
#.#. -> #.#. -> #.#. -> ...
#.#.    #.#.    #.#.
```

with populations `7,6,6,...`. Hence it violates `(W_k)` by one cell for every
`k>=3`, while its period-one tail has density exactly `1/2`. This is the
minimal-area obstruction for those window lengths.

These are counterexamples to the proposed finite lemmas, not to the cycle
conjecture: neither transient lies on a high-density temporal cycle. They
redirect a proof toward a genuinely configuration-dependent telescoping
potential (with spatial face terms or an equivalent projectively coherent
discharging rule). The displayed scalar combination of birth/death balance,
king-grid degrees, and edge counts cannot suffice, and neither can any finite
uncorrected time average.

`temporal_charging_obstruction.py` independently reapplies B3/S23, checks all
incidence counts above, exhausts the `3 x 3` state space, and certifies all
prefix lengths by decomposing each finite trajectory into its preperiod and
cycle.

## Exact `6 x 12` strip-pyramid bound

`pyramid_6x12.cert` assigns nonnegative integer weights to a `6 x 12`
slice at time `t`, its determined central `4 x 10` slice at `t+1`, and
the determined central `2 x 8` slice at `t+2`. The weights sum to
1,000,004. Exact max-plus row dynamic programming exhausts all `2^72`
initial slices symbolically and proves maximum live weight 555,468.
Translation averaging therefore gives

```
555468/1000004 = 138867/250001.
```

The certificate is only 36 lines. `pyramid_6x12_verify.cpp` reads the
integer artifact, checks its geometry and weight sum, independently
reapplies B3/S23, and computes the exact maximum without an LP solver.
As with the `6 x 10` level, no optimality claim is made for this rounded
weighting.

## Exact `6 x 10` strip-pyramid bound

`pyramid_6x10.cert` assigns nonnegative integer weights to a `6 x 10`
slice at time `t`, its determined central `4 x 8` slice at `t+1`, and
the determined central `2 x 6` slice at `t+2`. The weights sum to
1,000,004. Exact max-plus row dynamic programming exhausts all `2^60`
initial slices symbolically and proves maximum live weight 555,788.
Translating the weighted shape over a space-time torus therefore gives

```
555788/1000004 = 138947/250001.
```

This is strictly below `43578/78167`. `pyramid_6x10_search.py`
reproduces the weighting by reflection-reduced sparse LP column
generation and rounds it to a common integer grid. The rounding and
floating-point optimization are not trusted: `pyramid_6x10_verify.cpp`
reads only the integer artifact, reapplies B3/S23, checks its weight
sum, and independently computes the exact maximum using the C++17
standard library. No claim is made that this rounded weighting is the
exact optimum of the `6 x 10` hierarchy.

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
python pyramid_obstruction.py
python temporal_charging_obstruction.py
g++ -O3 -std=c++17 pyramid_verify.cpp -o pyramid_verify
./pyramid_verify pyramid_6x6.cert
g++ -O3 -std=c++17 pyramid_6x8_verify.cpp -o pyramid_6x8_verify
./pyramid_6x8_verify pyramid_6x8.cert
g++ -O3 -std=c++17 pyramid_6x10_verify.cpp -o pyramid_6x10_verify
./pyramid_6x10_verify pyramid_6x10.cert
g++ -O3 -std=c++17 pyramid_6x12_verify.cpp -o pyramid_6x12_verify
./pyramid_6x12_verify pyramid_6x12.cert
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
python pyramid_6x10_search.py
python pyramid_6x12_search.py
python verify.py
python strip2_verify.py
```

The search scripts enumerate or separate legal B3/S23 evolutions and use
SciPy/HiGHS; the pyramid search additionally uses OR-Tools CP-SAT.
Floating-point and solver results are treated only as certificate
discovery. The stored outputs are accepted only by the exact,
solver-independent verifiers.
