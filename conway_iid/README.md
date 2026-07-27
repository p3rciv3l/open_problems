# Exact finite-time Conway Life probability

This directory computes

\[
q_t(p)=\Pr(X_t(0,0)=1)
\]

for Conway Life on the infinite square grid when the time-zero cells are
independent Bernoulli(\(p\)) variables. The implementation is exact for
\(t=0,1,2\), uses only the Python standard library, and emits integer
coefficients.

See [`GLOBAL_ACTIVITY.md`](GLOBAL_ACTIVITY.md) for separate rigorous results
on infinitely many changes at every finite time and almost-sure spatial
density at each fixed time. Those results do not assert local nonfixation or
convergence of the densities as time tends to infinity.

See [`ASYMPTOTICS.md`](ASYMPTOTICS.md) for the exact verified leading terms at
time three, a local-fixation dichotomy, and precise blockers encountered by a
full time-three frontier computation and the proposed asymptotic arguments.

## Finite-time theorem

The state of the origin at time \(t\) is a Boolean function of only the
\((2t+1)^2\) initial cells in \([-t,t]^2\). Independence therefore gives the
finite identity

\[
q_t(p)=\sum_{k=0}^{(2t+1)^2} N_{t,k}p^k(1-p)^{(2t+1)^2-k},
\]

where \(N_{t,k}\) is the integer number of weight-\(k\) assignments in the
backward light cone that make the origin alive. This proves that \(q_t\) is a
polynomial and makes the calculation an infinite-grid result: no boundary
condition or limiting argument is involved.

A finite torus gives the same answer only when its wraparound identifications
do not merge cells in this cone. In particular, a torus with side length at
least \(2t+1\), viewed through an injectively embedded cone, can be used as a
finite-time experiment. Smaller tori generally compute a different
probability because nominally distinct cone variables are forced to agree.

## Algorithm and exact results

`life_probability.py` constructs each intermediate cell as a reduced ordered
binary decision diagram (ROBDD), using row-major order on the initial cone.
Dynamic programming builds the “exactly 2” and “exactly 3” neighbor predicates.
A weighted traversal of the final BDD counts satisfying assignments by Hamming
weight, including variables skipped by BDD reduction. The reported
`weight_counts` are the \(N_{t,k}\); `power_coefficients` are the coefficients
of \(1,p,p^2,\ldots\) after exact integer expansion.

The results are:

* \(q_0(p)=p\).
* \(q_1(p)=84p^3-448p^4+980p^5-1120p^6+700p^7-224p^8+28p^9\).
* For \(t=2\), the nonzero \(N_{2,k}\), for \(k=3,\ldots,18\), are
  `22, 1092, 10902, 52808, 159532, 352308, 662834, 1136852, 1653846,
  1844296, 1487120, 813480, 273548, 49756, 3962, 72`.

In the ordinary power basis,

```text
q_2(p) =
  22 p^3 + 608 p^4 - 6948 p^5 + 30208 p^6 - 63870 p^7
  + 38892 p^8 + 151610 p^9 - 569196 p^10 + 1306902 p^11
  - 2572808 p^12 + 4261710 p^13 - 5534604 p^14
  + 5602594 p^15 - 4928012 p^16 + 4695884 p^17
  - 5050812 p^18 + 4913444 p^19 - 3659272 p^20
  + 1946322 p^21 - 705996 p^22 + 163388 p^23
  - 21168 p^24 + 1102 p^25.
```

Thus the exact low-density leading behavior is \(q_1(p)=84p^3+O(p^4)\)
and \(q_2(p)=22p^3+608p^4+O(p^5)\). The coefficient 22 also says exactly
22 three-live-cell assignments in the 25-cell time-two cone lead to a live
origin.

## Running and verification

```bash
python life_probability.py 2
python life_probability.py 2 --monte-carlo 100000 --p 0.3 --seed 20260727
python -m unittest -v
```

At \(p=0.3\), the exact value is `0.28954603294586834`; the seeded 100,000-trial
run above gives `0.28956`.

The tests independently exhaust all \(2^9\) inputs at time one. For time two,
`exhaustive_t2.c` directly scans all \(2^{25}=33,554,432\) cone assignments
and its 26 counts are compared with the BDD result. This C verifier deliberately
shares no BDD or polynomial code. Tests also compare seeded Monte Carlo at
\(p=0.1,0.3,0.5\) against the exact values.

The current exact command is intentionally capped at \(t=2\). The initial cone
already grows from 25 variables at \(t=2\) to 49 at \(t=3\), while this simple
row-major ROBDD construction creates about 260,000 nodes at \(t=2\). ROBDD
size is highly variable-order dependent and can grow exponentially; no useful
time-three resource bound follows from the time-two run. Advancing farther
will require better variable ordering, frontier elimination, symmetry
quotienting, or component decomposition rather than silently attempting an
unbounded computation.
