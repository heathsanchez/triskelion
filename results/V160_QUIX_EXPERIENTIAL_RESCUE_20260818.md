# V160 Quix Experiential Rescue — 2026-08-18

## Status
PASS — bounded executable coding experiential rescue.

Workflow run: `32060246275`
Head SHA: `8a8e7a80886a38542a38c75e9e5cba560448edb4`
Artifact: `v160-quix-experiential-rescue`
Artifact SHA256: `9cc8de90d3b28f9f7882ff1191d289c1d104601956c3178c319d6926f8812fc8`

## Frozen protocol
Start from the already successful QuixBugs V12 AB checkpoint. Collect two prior executable-verified repair experiences for each earlier task on worlds 80 and 81; anti-unify those verified lines into a generic variable-renaming template and freeze it. Restart from the same AB checkpoint and train only task C, with no A/B replay, until the first protected A/B regression. Freeze that first-regression checkpoint and compare neural-only, raw verified memory, compiled experiential map, and shuffled-map arms on held-out worlds 100..107.

## Prior verified experiences / learned maps
A experiences:
- `stack80.append(item80)` — verifier PASS
- `stack81.append(item81)` — verifier PASS
- learned template: `stack{K}.append(item{K})`

B experiences:
- `return [num80]` — verifier PASS
- `return [num81]` — verifier PASS
- learned template: `return [num{K}]`

Starting protected scores from the stable AB checkpoint:
- A 8/8
- B 8/8
- C 0/8

## Interference curve
C-only consolidation, original LR and batch size, no A/B replay:
- step 1: A 8/8, B 8/8, C 8/8
- step 2: A 8/8, B 8/8, C 8/8
- step 3: A 8/8, B 8/8, C 8/8
- step 4: A 8/8, B 8/8, C 8/8
- step 5: A 0/8, B 0/8, C 8/8

First-regression checkpoint:
`river://8c23d218-606e-4b90-a4df-d8a9c86ef554/weights/v160_first_regression_step5`

The step-5 neural outputs preserve most repair content but lose the final closing delimiter:
- A examples become `stack100.append(item100` rather than `stack100.append(item100)`.
- B examples become `return [num100` rather than `return [num100]`.
The executable verifier therefore correctly rejects all A/B outputs.

## Frozen-weight arm comparison
Prior-task executable hits, A+B total out of 16:
- neural only: **0/16**
- raw verified memory in prompt: **0/16**
- compiled experiential map: **16/16**
- shuffled A/B maps: **0/16**

Per task under compiled experiential map:
- A 8/8
- B 8/8
- C 8/8 (left neural-only; weights unchanged)

Thus the compiled map restores the earlier executable repair capabilities without changing the regressed neural weights or sacrificing the newly learned C capability. Raw prior examples alone do not rescue the model, and the same-budget wrong map does not rescue it.

## Verdict
`PASS_REAL_CODING_EXPERIENTIAL_RESCUE`

## Supported bounded statement
Under this frozen QuixBugs variable-renaming protocol, verified prior coding experiences can be compiled into an explicit reusable map that causally preserves/restores earlier executable repair behavior after later neural interference. At the first-regression checkpoint the explicit map yields 16/16 prior-task verifier passes versus 0/16 for neural-only, 0/16 for raw verified memory, and 0/16 for a shuffled-map ablation, while the new task remains 8/8.

## Claim boundary
This does **not** establish unrestricted program repair, natural-world operator discovery, or open-ended self-improvement. The map is a simple anti-unified repair schema over a supplied variable-renaming family, and the observed regression is specifically a syntactic termination/delimiter failure after C-only consolidation. The result supports the narrower causal claim that compiled verified experience can remain executable and correctly scoped when the neural realization becomes temporarily unreliable.

## Next separator
The strongest next test should remove the trivial numeric alpha-renaming scaffold: learn a structural repair operator from verified prior programs with heterogeneous variable names / AST contexts, then test transfer and interference rescue on held-out code where the correct edit is not recoverable by substituting a world-id slot. Raw-memory and shuffled/operator-mismatched ablations remain mandatory.
