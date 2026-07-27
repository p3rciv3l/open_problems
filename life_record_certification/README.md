# Exact-period-2 population certificate

This directory certifies one deliberately small claim:

> On the `4 x 4` finite torus under Conway's `B3/S23` rule, the minimum
> time-0 population of a state having exact period 2 is **3**.

The objective is the population at time 0. A period-2 orbit can have unequal
populations at its two phases; this claim does not minimize their maximum or
sum.

## Certificate contents

`artifacts/witness.json` is an attaining three-cell orbit. The independent
`scripts/check_witness.py` directly applies Life twice, with wrapped
coordinates, and checks that the two states differ.

There is one DIMACS file for every strictly better integer bound:

| bound | CNF | proof |
|---:|---|---|
| 0 | `artifacts/cnf/period2-pop-le-0.cnf` | `artifacts/proofs/period2-pop-le-0.drat` |
| 1 | `artifacts/cnf/period2-pop-le-1.cnf` | `artifacts/proofs/period2-pop-le-1.drat` |
| 2 | `artifacts/cnf/period2-pop-le-2.cnf` | `artifacts/proofs/period2-pop-le-2.drat` |

Variables 1--16 and 17--32 are the two phases in row-major order. For each
cell and each of the 512 assignments to its center and eight neighbors, one
clause fixes the next-phase value. Both transitions are encoded. Variables
33--48 are XORs of corresponding phase cells, and their disjunction excludes
period 1. The final clauses are the direct subset encoding of the stated
at-most bound.

`scripts/check_cnf_encoding.py` separately reconstructs that specification and
requires exact clause-for-clause equality. The checked-in text DRAT proofs end
in contradiction. `scripts/verify_proofs.sh` compiles and runs the vendored
independent `drat-trim` checker. `artifacts/manifest.json` records byte counts
and SHA-256 hashes for every artifact.

Run all checks:

```sh
python3 -m unittest discover -s tests -v
```

To regenerate the logical inputs and manifest without a SAT solver:

```sh
python3 scripts/generate.py
```

To regenerate proofs, set `CADICAL` to a CaDiCaL executable:

```sh
CADICAL=/path/to/cadical scripts/build_certificates.sh
```

The checked-in proofs were produced by CaDiCaL 3.0.1 from commit
`c60730422e758ef1cebe7aeddf2dda31c996bf04` using `--no-binary`. Solver output
is retained beside each proof. The solver is not in the trusted base: its
output is accepted only after DRAT checking.

## Trust boundary

Proof logging and independent proof checking are available here. The DRAT
check establishes only that each exact checked-in CNF is unsatisfiable.
Connecting those CNFs to the stated Life problem requires trusting or
reviewing the short Python specification checkers and Python's execution.
Connecting the upper bound requires the same for the independent witness
checker. Checking DRAT additionally trusts the C compiler/runtime and the
vendored `drat-trim.c` at upstream commit
`2e3b2dc0ecf938addbd779d42877b6ed69d9a985`; its upstream license is included.
The manifest detects changes relative to itself but is not a signature and
provides no authenticity if it and the artifacts are replaced together.
