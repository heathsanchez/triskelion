# V83 Natural IVAG — QuixBugs

**Verdict:** `MIXED_NATURAL_IVAG_V83`

**Primary run:** `31779917767`  
**Head:** `e9e6f84eb63d99c20f777184e2ed709c0400c207`  
**Artifact:** `9211349228`  
**Artifact SHA-256:** `a960ee85b4dacdb5c3a6780c1ef8761f57c3932e09e763096848186f5d2c3abe`

External corpus: `jkoppel/QuixBugs` at commit `4257f44b0ff1181dedaedee6a447e133219fcebf`. Correct implementations were not read during discovery.

Two independently hash-ordered curricula converged on the same two minimum-description one-token repair schemas:

- `<= -> <` from `find_first_in_sorted`;
- `< -> <=` from `quicksort` (with `> -> >=` tied at the same description length on that task).

However, the frozen ten-task held-out probe frontier remained empty before and after both extensions in both curricula. Therefore:

- natural pre-existing corpus: **PASS**;
- at least one minimum extension in each curriculum: **PASS**;
- independent extension-set convergence: **PASS**;
- strict held-out closure growth: **FAIL**;
- three-generation developmental causality: **FAIL BY DESIGN** under this constructor, because all 26 token-pair schemas are candidate-discoverable from the start.

## Scientific meaning

V83 separates **reusable/minimal natural repair** from **developmentally valuable primitive**. Natural curricula can converge on the same compact repairs without those repairs enlarging a broader held-out closure frontier. The next constructor should therefore be evaluated by developmental gain, not merely recurrence or local repair success.

This is evidence against treating any repeated minimal repair as a cognitive primitive automatically.
