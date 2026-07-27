# Bounded glider-synthesis experiments (problem 10)

This directory provides an executable finite experiment, not a proof that a finite synthesis basis exists.

## Model

`LocalMove` records exact input and output still-life contexts, glider phases at their boundary generations, duration, and a closed affected box. `TimedGlider` validates its five cells by requiring exactly one cell of diagonal displacement after four generations; zero-translation five-cell still lifes are rejected. A move is valid only when unbounded-plane Life simulation reaches its declared output exactly and every cell outside the affected box remains equal to the input context throughout. Verification reports the bounding box of observed non-baseline live cells, or deterministically uses the declared affected box when a quiescent/identity move has no such cells.

Canonical keys take the lexicographically least representation over all eight square symmetries after translation. Names are metadata and do not affect equivalence. `bounded_closure` builds a finite graph of whole-context rewrites. It deliberately does not infer subpattern embedding, non-interaction, or arbitrary repetition.

## Certified local embedding

`embedding.py` adds a sufficient, machine-checkable noninteraction semantics. If independently evolved finite patterns `A_t` and `B_t` have Chebyshev separation at least 3 at every generation through `T`, no radius-1 Life neighbourhood contains live cells from both. Therefore

```text
Life(A_t ∪ B_t) = Life(A_t) ∪ Life(B_t),
```

and induction gives the union identity through generation `T`. `certify_noninteraction` checks the separation hypothesis and the resulting trace identity. `independent_union` uses pairwise certificates to compose any finite collection of equal-duration local moves. This is a sufficient lemma, not a claim that closer traces necessarily interact.

## Rewindable collision corpus

`corpus.py` contains eight distinct two-glider components derived by bounded collision search. Unlike the original three demonstration edges, each pair approaches from different directions and is independently rewound 40 generations to verify an autonomous approach. Every declared forward reaction is also independently simulated to its first still-life state. The exact output-population spectrum is:

```text
0, 4, 6, 7, 8, 8, 16, 24
```

The outputs include annihilation, block, beehive, loaf, two distinct two-block constellations, a four-block constellation, and a 24-cell constellation. This corpus is substantial enough to exercise canonicalization, rewind certification, and local composition, but it is not asserted to be the complete set of 71 two-glider collisions or a universal basis.

`candidate_basis_report` treats these eight canonical reactions as the finite candidate **B8**. Its exact whole-context closure from empty has eight contexts and then stalls, while the composition lemma closes it under sufficiently separated finite unions. The report keeps `universal_claim` false: B8 is a concrete tested candidate with a useful sparse closure, not evidence that every synthesis factors through it.

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

## Block-array constructions

`BlockArrayInstance` models finite `m×n` arrays with explicit horizontal and vertical gaps. `assess` asks whether one exact array is in one computed finite closure and always keeps `implies_finite_basis_theorem` false. Thus observations about arrays are not treated as either proving or following from a universal finite-basis theorem.

Two stronger results are kept separate:

1. `construct_spaced_block_array` is a complete construction for every finite `m×n` and gaps of at least 6 cells in each nontrivial direction. It places `mn` translated copies of the rewindable two-glider block reaction and proves pairwise independence from their complete four-generation traces. The construction costs exactly `2mn` gliders. It does not cover the standard one-cell-gap block agar.
2. `published.py` encodes Jason Summers' published eight-glider `2×4 → 2×5` extension component from [LifeWiki's block-array page](https://conwaylife.com/wiki/Block_array). The input is decomposed into eight validated gliders plus a still-life context and independently settles to ten blocks at generation 68. Direct simulations verify the same right-end extension for widths 4 through 29. Life's radius-one domain of dependence then proves it for every width `n ≥ 4`: at the width-29 cutoff the nearest omitted prefix block is two cells beyond the full generation-68 causal radius of the finite catalyst/glider perturbation. Outside that cone the `2×n` array is already a still life.

The second result proves the inductive extension step, conditional on constructing its still-life catalyst context and a starting `2×4` array. It does not supply the missing arbitrary-height standard-gap construction; the general standard `m×n` problem remains open.
