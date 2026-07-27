# Problem 9: isolated orthogonal translating Life waves

This is an exact finite-state transfer search for a Life configuration with

```
C(t + 10, x + 6, y) = C(t, x, y)
```

and certified semi-infinite background tails. There is no longitudinal seam:
the search scans every integer `x` from an exact left background tail and only
accepts a witness after its boundary state returns to the exact right tail.
Such a finite path can be pumped in time by the translation relation and is an
isolated `3c/5` orthogonal wave, not a periodic wave train.

## Stated background and finite class

The background is the explicit static 2x2-block lattice in
`backgrounds/block_lattice_6x4.json`. Its x period 6 makes it compatible with
displacement 6; its y period and the searched cylinder width are 4. The code
checks both Life evolution and translation compatibility before searching.

A transfer column contains all 40 bits `C(t,x,y)` for `0 <= t < 10` and
`0 <= y < 4`. A boundary retains seven consecutive columns. Appending column
`x+1` decides every Life equation centered at `x`; for the last time slice it
uses the exact identity `C(10,x,y) = C(0,x-6,y)`.

The checked class bounds each spacetime column to at most two bits different
from the stated background column. This gives 821 candidates per background
phase. Rather than testing that raw alphabet at every boundary, the exact
expander solves each four-bit transverse row independently and combines only
row solutions whose total Hamming cost is at most two. This is equivalent to
enumerating all 821 columns, not a relaxation.

Breadth-first search exhausts the reachable boundary-state graph from the
background cycle. An `absent` result is exact only for this finite state class.
The JSON preserves state/edge counts and a deterministic SHA-256 digest of the
ordered reachable graph so the certificate can be reproduced:

```sh
python -m life_velocities.search_transfer
python -m life_velocities.verify_transfer
```

The preserved two-deviation result is `absent` after exhausting 371,885
reachable boundary states and 371,885 edges. It strictly contains the earlier
one-deviation class.

Negative-spaceship searches and elementary speed/period bounds are different
questions and are intentionally not encoded or claimed here.
