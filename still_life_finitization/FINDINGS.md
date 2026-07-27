# Scoped findings: still-life finitization

## Scope

These experiments use the following finite problem only. A rectangular core is
fixed cell-for-cell from an infinite periodic Life still life. For margin `m`,
all cells outside the core expanded by `m` in each direction are required dead.
The question is whether the cells in the margin can make the whole finite
configuration a still life. This is not a result about arbitrary finite subsets,
other cellular automata, or margins measured non-uniformly.

`experiments/results.json` records 64 cases produced by
`experiments/run_experiments.py` using python-sat 1.9.dev7's `cadical195`
backend. It contains 123 solver calls: 59 UNSAT and 64 SAT. Each first SAT
witness passed the separate direct checker. The largest call had 256 variables
and 46,140 clauses. For each call the result retains the exact variable and
clause counts, solver counters, and a SHA-256 digest of the clause stream.

## Exact observations

The entries below give the proved minimum uniform margins. A value `m` means
that every margin below `m` was UNSAT and margin `m` was SAT.

| Family | Window parameter | Minimum margins |
|---|---|---|
| 4x4 block agar, origin (0,0), square | side 1..12 | `1,0,0,0,1,0,0,0,1,0,0,0` |
| 4x4 block agar, origin (1,1), square | side 1..12 | `1,1,1,1,1,1,1,1,1,1,1,1` |
| 5x5 tub agar, origin (0,0), square | side 1..12 | `0,1,0,0,0,2,1,0,0,0,2,1` |
| 5x5 tub agar, origin (2,2), square | side 1..12 | `0,0,0,0,1,2,2,2,2,2,2,2` |
| 5x5 tub agar, origin (0,0), height-1 strip | width 1..16 | `0,1,1,1,1,1,1,1,1,2,2,2,2,2,2,2` |

The block sequences reflect cuts through separated 2x2 blocks: period-aligned
cuts often already contain complete finite blocks, while the shifted phase
consistently needs one layer. The tub cases show a small growth pattern. In the
dead-phase square family the observed minimum rises from 0 to 1 to 2 and stays
at 2 through side 12. In the height-1 strip family it rises from 0 to 1 to 2
and stays at 2 through width 16. Aligned tub squares instead oscillate with the
tile phase.

## Interpretation limits

The data establish only the listed finite minima. The apparent plateaus may be
periodic boundary effects, and the observed rises do not imply that margins are
unbounded. No extrapolation beyond the tested windows is justified. UNSAT
results are solver results tied to the recorded deterministic CNFs; this run
did not retain independently checkable UNSAT proof traces. SAT sides are
stronger operationally because every emitted model is independently checked
against the Life rule and the dead-exterior condition.
