# Asymptotic status and the time-three frontier

This note records what can currently be proved from the Bernoulli initial
field, and where the attempted exact and asymptotic arguments stop. It does
not claim convergence or local fixation for any \(0<p<1\).

## A rigorous local-fixation dichotomy

Fix \(p\), and let

\[
Y(z)=\mathbf 1\{X_t(z)\ne X_{t+1}(z)\text{ for infinitely many }t\},\qquad
\theta(p)=\mathbb P(Y(0)=1).
\]

**Proposition.** Exactly one of the following holds almost surely:

1. every cell changes only finitely many times; or
2. the set of cells that change infinitely often has spatial density
   \(\theta(p)>0\).

**Proof.** The whole field \(Y\) is a measurable translation-equivariant
factor of the initial Bernoulli field, so it is stationary and ergodic. The
pointwise ergodic theorem gives

\[
\lim_{n\to\infty}\frac1{(2n+1)^2}\sum_{z\in[-n,n]^2}Y(z)=\theta(p)
\quad\text{almost surely}.
\]

If \(\theta(p)>0\), this is alternative 2. If \(\theta(p)=0\), then
\(\mathbb P(Y(z)=0)=1\) for each \(z\); the countable intersection over
\(\mathbb Z^2\) is alternative 1. \(\square\)

In alternative 1, \(X_t(0)\) has an almost-sure limit, so dominated
convergence proves that \(q_t(p)=\mathbb E X_t(0)\) converges. The converse is
not established: convergence of one-time marginals need not imply that sample
paths fixate.

The global-activity theorem in `GLOBAL_ACTIVITY.md` does not choose between
these alternatives. It supplies infinitely many changing cells at each
fixed time, but those cells may be different at different times.

## Exact time three: verified leading terms

The time-three cone has 49 variables. Direct enumeration restricted by
initial Hamming weight gives

```text
k             0  1  2   3     4      5
N_{3,k}       0  0  0  22  1536  39108
```

`q3_low_weight.py` enumerates the \(\binom{49}{k}\) subsets directly. The
separate `verify_q3_low.c` implementation reproduces all six counts without
using the Python transition code. Consequently,

\[
q_3(p)=22p^3+524p^4-7242p^5+O(p^6)
\quad (p\downarrow0).
\]

This is a leading-term result, not the full exact polynomial.

## Full \(q_3\) frontier attempt and blocker

A row frontier was tried in the order of the seven initial rows. Once three
input rows are present it emits a width-five time-one row; three such rows
emit a width-three time-two row. A state retains the last two rows at each
available level. Exact deduplication of reachable Boolean frontier states
gave:

```text
initial rows consumed       2       3         4          5
reachable states        16,384  251,202  6,612,404  37,521,774
```

The five-row reachability pass alone used about 309 MB. Weighted model
counting needs, for every state, a polynomial in the number of initially live
cells; reachability bits alone are insufficient. Even one dense 50-entry
unsigned-integer vector per five-row state would require about 15 GB, before
hash-table and next-frontier storage. The next transition also has
\(37,521,774\times128\), about \(4.8\) billion, state/row pairs. Thus this
straight row ordering does not fit the present implementation budget.
Obtaining all of \(q_3\) requires a materially better ordering, compressed
polynomial representation, meet-in-the-middle contraction, or symmetry
quotient, not merely extending the \(t=2\) ROBDD.

## Why the proposed asymptotic routes do not yet close

These are specific logical blockers, not impossibility theorems.

* **Finite-range dependence:** at fixed \(t\), dependence range is finite,
  but it grows linearly with \(t\). The fixed-time ergodic argument therefore
  gives no uniform temporal mixing or Cauchy estimate for \(q_t(p)\).
* **Protected oscillators:** a radius-\(t+2\) dead square protects a blinker
  only through time \(t+1\). Its cylinder probability is
  \(p^3(1-p)^{(2t+5)^2-3}\), which tends to zero superexponentially. These
  finite-horizon events prove global activity, not repeated changes at a
  fixed cell.
* **Sparse clusters:** Life is not an eroder. A finite glider travels forever,
  and finite still lifes and oscillators persist. Hence a low-density
  Bernoulli field cannot be handled by a theorem whose key hypothesis is
  that every isolated finite island disappears in time proportional to its
  diameter.
* **Monotone coupling:** the Life map is not attractive. If three neighbors
  of a dead center are alive, the center is born; adding a fourth live
  neighbor suppresses that birth. Thus inclusion of initial live sets is not
  preserved, so the standard monotone coupling to subcritical percolation
  does not apply directly.

No proof of convergence or local fixation on a nontrivial interval of \(p\)
follows from these methods. The proposition above and the exact low-density
terms are the proof-grade asymptotic progress; an interval theorem remains
open in this work.
