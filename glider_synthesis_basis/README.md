# Bounded glider-synthesis experiments (problem 10)

This directory provides an executable finite experiment, not a proof that a finite synthesis basis exists.

## Model

`LocalMove` records exact input and output still-life contexts, glider phases at their boundary generations, duration, and a closed affected box. `TimedGlider` validates its five cells by requiring exactly one cell of diagonal displacement after four generations; zero-translation five-cell still lifes are rejected. A move is valid only when unbounded-plane Life simulation reaches its declared output exactly and every cell outside the affected box remains equal to the input context throughout. Verification reports the bounding box of observed non-baseline live cells, or deterministically uses the declared affected box when a quiescent/identity move has no such cells.

Canonical keys take the lexicographically least representation over all eight square symmetries after translation. Names are metadata and do not affect equivalence. `bounded_closure` builds a finite graph of whole-context rewrites. It deliberately does not infer subpattern embedding, non-interaction, or arbitrary repetition.

Run the reproducible report and tests from the repository root:

```sh
python -m glider_synthesis_basis.cli
python -m unittest discover -s glider_synthesis_basis/tests -v
```

## Exact built-in findings

The three declared rewrites are each independently simulated:

- two gliders produce one block and stabilize at generation 8, with activity box `[-3,3] × [0,5]`;
- two gliders produce one boat and stabilize at generation 8, with activity box `[-4,0] × [-3,3]`;
- a preserved block plus the first collision produces a particular two-block still life at generation 8; its changing activity has the first reaction's box.

For this exact three-edge graph, closure from the empty context within three rewrites has four canonical contexts, containing 0, 4, 5, and 8 live cells. The specific horizontal `1×2` block array with four dead columns between its two-cell-wide blocks has a two-step witness. A standard-gap `2×2` array is absent from this graph; absence is only “not reached by this supplied bounded graph,” not impossibility.

## Separate block-array question

`BlockArrayInstance` models finite `m×n` arrays with explicit horizontal and vertical gaps. `assess` asks whether one exact array is in one computed finite closure and always keeps `implies_finite_basis_theorem` false. Thus observations about arrays are not treated as either proving or following from a universal finite-basis theorem.
