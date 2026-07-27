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

## Stationary spacetime limits and mass balance

There is a useful all-\(p\) conclusion after averaging in time, but it does not
decide fixation. Let \(\mu_t=F^t_*\mu_p\), where \(F\) is the Life map and
\(\mu_p\) is Bernoulli(\(p\)), and set

\[
\nu_T=\frac1T\sum_{t=0}^{T-1}\mu_t.
\]

**Proposition.** Every sequence \(T_j\to\infty\) has a subsequence along which
\(\nu_{T_j}\) converges weakly to a spatially translation-invariant,
\(F\)-invariant probability measure \(\nu\). Along the same subsequence,

\[
\frac1{T_j}\sum_{t=0}^{T_j-1}q_t(p)\longrightarrow
\nu\{x:x(0)=1\}.
\]

**Proof.** The configuration space \(\{0,1\}^{\mathbb Z^2}\) is compact
metrizable, so its probability measures are weakly sequentially compact.
Every \(\mu_t\), hence every limit, is translation invariant. For every
continuous \(f\),

\[
\int f\,d(F_*\nu_T)-\int f\,d\nu_T
=\frac{\int f\,d\mu_T-\int f\,d\mu_0}{T}\longrightarrow0.
\]

Continuity of the cellular-automaton map \(F\) makes each limit
\(F\)-invariant. Taking the cylinder function \(f(x)=x(0)\) gives the density
claim. \(\square\)

Write \(b_t\) and \(d_t\) for the probabilities that the origin is respectively
born or dies from time \(t\) to \(t+1\). Then the exact telescoping identity

\[
\frac1T\sum_{t=0}^{T-1}(b_t-d_t)
=\frac{q_T(p)-q_0(p)}T\longrightarrow0
\]

shows asymptotic birth/death balance in time average. Under every invariant
limit \(\nu\), births and deaths have equal intensity.

Mass transport gives two further exact, but noncontractive, inequalities:

\[
q_{t+1}\leq3q_t,\qquad b_t\leq\frac83q_t.
\]

For the first, every cell alive at \(t+1\) has at least three live cells in
its closed \(3\)-by-\(3\) predecessor neighborhood. Count these incidences;
each time-\(t\) live cell is in nine such neighborhoods. For the second, each
birth has exactly three live neighbors, while a time-\(t\) live cell can be
adjacent to at most eight births. Neither coefficient is below one, so these
bounds provide no decay or Cauchy estimate for \(q_t\).

## Entropy cannot by itself charge activity

Spatial entropy \(h(\mu_t)\) is nonincreasing because \(\mu_{t+1}\) is a
factor of \(\mu_t\), so \(h(\mu_t)\) has a limit. There is, however, no
universal inequality that lower-bounds entropy loss by a positive constant
times the density of changing cells.

To see this exactly, partition the plane into \(10\)-by-\(10\) tiles. At each
tile center independently place either nothing, a horizontal blinker, or a
vertical blinker, with probabilities \(1/2,1/4,1/4\). Blinkers in distinct
tiles cannot interact. Life fixes the empty choice and swaps the two blinker
choices. Averaging this product measure over the 100 spatial offsets produces
a fully translation-invariant and \(F\)-invariant measure. It has positive
spatial entropy, live-cell density \(3/200\), and changing-cell density
\(1/50\). Its entropy loss is zero while its activity is positive. Thus an
entropy/activity inequality would need a property special to the Bernoulli
orbit, not merely stationarity, finite range, or positive entropy.

The same example shows why a stationary subsequential limit does not decide
the dichotomy: invariant limits with persistent activity exist, while the
all-dead point mass is an invariant limit with none. A new selection argument
would have to prove which invariant measures can actually arise from
\(\mu_p\).

## Finite forcing and the tail obstruction

The event \(Y(0)=1\) from the dichotomy proposition is not a tail event of the
initial Bernoulli field. Starting from the all-dead configuration gives
\(Y(0)=0\); changing only three cells to make the origin an arm of an isolated
blinker gives \(Y(0)=1\). Therefore Kolmogorov's tail zero-one law cannot
decide \(\theta(p)\).

A finite cylinder that forced a chosen cell to change forever for every
completion outside the cylinder would amount to a finite structure protected
against arbitrary incoming Life activity. The protected-blinker cylinders
used for global persistence do not have this property: their guarantee ends
when the finite light cone reaches the edge of the dead square. No such
infinite-time forcing structure is established here. Without one, positive
probability of a finite oscillator in a quiet finite neighborhood cannot be
promoted to positive probability of local nonfixation.

Consequently, stationary limits prove existence only after subselection,
mass transport proves balance but not contraction, entropy admits active
invariant counterexamples, and finite-energy/tail arguments do not apply.
These mechanisms do not decide the fixation dichotomy or convergence of
\(q_t(p)\) for any nontrivial interval of \(p\).
