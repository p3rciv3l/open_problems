# Problem 9: orthogonal translating Life waves

This directory contains an exact finite-quotient SAT/SMT search targeting
displacement 6 in period 10 (`3c/5`). It starts with user-selected small strip
lengths and transverse widths:

```sh
python -m pip install -r life_velocities/requirements.txt
python -m life_velocities.search --lengths 4:8 --widths 1:4
```

Each JSON file is retained whether the bounded instance is `sat`, `unsat`, or
`unknown`. `unsat` is an exact result for that fully specified quotient;
timeouts are recorded as `unknown`, never as UNSAT. SAT files contain all live
quotient cosets and background cells and are independently simulated over
three copies on both sides of every temporal and spatial seam.

## Exact encoding

For cell state `C(t,x,y)`, with transverse coordinate periodic modulo `W`, the
finite quotient explicitly imposes

```
C(t + 10, x + 6, y) = C(t, x, y)       translation
C(t - S, x + L, y)  = C(t, x, y)       spatial seam and seam phase S
```

The quotient has `W * (10L + 6S)` Boolean cells. Life's B3/S23 rule is imposed
at every quotient cell. A separate background torus has independently chosen
time, x, and y periods. Guard columns at both ends equal that background at
the explicit `--background-phase`; at least one interior cell must differ.
By default the background must contain a live cell, and generation 10 must
differ from generation 0 at the same coordinates. The latter prevents a
stationary pattern from satisfying the translation equation merely because
the displacement vanishes modulo its spatial period.

This is sound as an infinite, doubly periodic wave train: any SAT assignment
lifts to all integer `(t,x,y)` and obeys Life everywhere. It does **not**
represent a single isolated wave with semi-infinite background on both sides,
because the spatial seam repeats the disturbance every `L` cells. Therefore a
SAT witness here must not be claimed as an isolated infinite wave. Proving or
finding that stronger object requires a transfer construction with certified
background tails (or an unbounded limit argument), which this finite quotient
does not provide.

Because a spatially periodic object can admit more than one equivalent
displacement, this encoding establishes the stated displacement relation and
non-stationarity, not a unique velocity modulo every possible spatial period.
