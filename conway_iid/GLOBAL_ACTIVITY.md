# Global activity and fixed-time density

Let \(X_t(z)\in\{0,1\}\) be Conway Life on \(\mathbb Z^2\), started from
i.i.d. Bernoulli(\(p\)) cells with \(0<p<1\).

**Theorem (global activity at every finite time).** Almost surely, for every
integer \(t\geq0\), infinitely many \(z\in\mathbb Z^2\) satisfy
\(X_t(z)\ne X_{t+1}(z)\).

**Proof.** Fix \(t\), put \(R=t+2\), and consider the cylinder event consisting
of a horizontal blinker at \((-1,0),(0,0),(1,0)\), with every other cell in
the Chebyshev square \([-R,R]^2\) dead. Its probability is

\[
a_t=p^3(1-p)^{(2R+1)^2-3}>0.
\]

Life has propagation speed at most one in Chebyshev distance. For the right
arm \(u=(1,0)\), every initial cell that can affect \(X_s(u)\), for
\(0\leq s\leq t+1\), lies in \(u+[-s,s]^2\), which is contained in
\([-R,R]^2\). Arbitrary cells outside the protected square therefore cannot
affect this arm through time \(t+1\). It follows the isolated period-two
blinker: \(X_s(u)=1\) for even \(s\) and \(0\) for odd \(s\). In particular,
it changes between times \(t\) and \(t+1\).

Now place infinitely many translates of this cylinder on pairwise disjoint
squares, for example along a sufficiently sparse horizontal lattice. The
events are independent and each has probability \(a_t\). The probability
that at most finitely many occur is zero (equivalently, apply the second
Borel--Cantelli lemma). Hence infinitely many distinct arm cells change from
\(t\) to \(t+1\), almost surely. Intersecting these probability-one events
over the countable set \(t=0,1,2,\ldots\) proves the theorem. \(\square\)

This is **global persistence of activity**. It does not say that the origin,
or any fixed finite window, changes infinitely often. The changing cells
supplied by the proof can move arbitrarily far away as \(t\) varies.

**Proposition (density at fixed time).** For each fixed \(t\), almost surely,

\[
\lim_{n\to\infty}\frac{1}{(2n+1)^2}
\sum_{z\in[-n,n]^2}X_t(z)=q_t(p)
=\Pr(X_t(0)=1).
\]

**Proof.** At fixed \(t\), \(X_t(z)\) is a translation-equivariant measurable
function of the finitely many initial variables in
\(z+[-t,t]^2\). Thus \(X_t\) is a finite-range factor of the Bernoulli shift.
The Bernoulli shift is ergodic, and every translation-equivariant factor of
an ergodic action is ergodic. The pointwise ergodic theorem for the square
Følner sequence \([-n,n]^2\) gives the displayed limit, whose expectation is
\(\mathbb E[X_t(0)]=q_t(p)\). \(\square\)

By another countable intersection, the fixed-time density statement may be
taken to hold simultaneously for all integer \(t\geq0\). It gives no
interchange of the limits in space and time and, in particular, does **not**
show that \(q_t(p)\) converges as \(t\to\infty\).
