# Adversarial safety experiments for Life

This directory treats two different quantifier structures with shared
simulation code.

* **Problem 6 / Immovable Object:** `check_bounded_flip` asks whether there
  exists an arbitrary assignment to every exterior cell in the protected
  cell's finite light cone that changes that cell at some generation
  `1..H`. The cells inside the declared protected rectangle are fixed,
  including its dead cells. Life transitions and the disjunction of possible
  flip times are encoded as CNF and decided by the included SAT solver. A SAT
  result includes an independently replayable exterior assignment and trace;
  UNSAT is a bounded universal certificate.
* **Problem 7 / single-glider-proof object:** `enumerate_interacting_attacks`
  universally enumerates four directions, four phases, and every integer lane
  whose isolated glider can Moore-interact with a finite still-life target.
  Translation along a lane is normalized upstream. `check_all_single_gliders`
  then checks each finite collision separately.

These quantifiers are intentionally not conflated. **Survival through a
bounded horizon does not solve the Immovable Object Problem**, whose exterior
is arbitrary and whose time quantifier is infinite. A glider sweep restricts
the adversary to one glider and is not evidence for arbitrary-exterior
survival.

Likewise, reaching a simulation timeout is not evidence that a collision has
settled. This toolkit certifies finite collision settling only when the entire
finite configuration repeats exactly (periodic by determinism), and certifies
recovery only when it equals the target exactly. Every other run is labeled
`unresolved_by_horizon`. Exhaustive finite lane enumeration currently requires
a still-life target; evolving targets need a separately certified finite
spacetime envelope/period criterion before the same claim can be made.

Run the checked examples and tests:

```sh
cd life_indestructibility
python3 generate_examples.py
python3 -m unittest discover -s tests -v
```

`examples/bounded_results.json` contains a one-tick UNSAT result and a SAT
block counterexample trace. `examples/block_single_gliders.csv` records every
enumerated block attack, not just selected collisions.
