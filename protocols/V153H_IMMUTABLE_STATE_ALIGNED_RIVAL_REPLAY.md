# V153H Immutable State-Aligned Rival Replay — Frozen Protocol

## Purpose

V153G established, without model or verifier calls, that the six distinct frozen raw-T1 call-2 rivals from V153 divide cleanly by source-state grounding: two apply only to the original buggy T2 state and four apply only after the frozen call-1 edit. None are ungrounded in both states.

V153D/E/F execution diagnostics are not admissible for exhaustive replay because their standalone use of `v145_precompiled_runner` can cache a candidate-mutated working tree as the reusable template before later replays. The original V153 run is not affected by that specific contamination because V151 `prepare_t2()` runs the untouched buggy baseline before arms, thereby prewarming the template from clean T2.

This diagnostic asks the smallest remaining question:

**When every frozen V153 rival is executed on the exact source state it demonstrably targets, does any rival solve T2?**

No new model calls are permitted.

## Frozen evidence

Source V153 artifact: run `31943774314`, artifact `v153-set-valued-rival-search`.

Required `V153_RESULT.json` SHA256:

`ae572174c253b47cef2db706254b45675a8c414feeb8d6bf7c86d516bd206057`

Task: BugsInPy `youtube-dl/32`.

Arm: `D_PLUS_RAW_T1`.

Frozen call-1 normalized payload SHA256:

`69002ebf51a2842e41639dd21d1d5c196ee65feac42470bdbef24067264f40bb`

Expected V153G grounding partition:

- CLEAN_ONLY: `583c8807e3546d8b5f1bef66691b6579c7819a2b2a32d065f4ade79cd57c876b`
- CLEAN_ONLY: `66836a81c4c370f95e354d6f6cc5c0daeaa7b4cd3046f59bc81b9b486c6dfd2e`
- POST_CALL1_ONLY: `e2412752d6ac269675bb75b704b06a809898b1c653655b9bd010ec12662fdb2b`
- POST_CALL1_ONLY: `da977ac0351961e7210a39b157e4905329e72034af5de75da63a562e8267f7f7`

The latter two appear in two frozen seeds each, yielding six seed-level rival instances but four unique payload hashes.

## Apparatus constraints

1. Do **not** import `v145_precompiled_runner`.
2. Use `bugsinpy_four_arm.checkout_buggy` directly for each replay, yielding an independent exact buggy checkout.
3. Before edits, SHA256 the production source file(s) and require the same clean-source hash for every replay.
4. For POST_CALL1 rivals, apply the frozen call-1 payload first, then assert the post-call-1 source hash is identical across every such replay.
5. Apply the selected frozen rival with the exact structured-edit protocol; no fuzzy matching, rebasing, repair, or mutation.
6. Invoke `bugsinpy_exact_runtime.native_test` directly. No reusable template may be created or consumed.
7. Treat duplicate payload hashes in different seeds as separate seed-level observations but also report unique-payload outcomes.

## Grounding assignment

Grounding is recomputed before native execution using exact sequential `old`→`new` semantics. The expected V153G partition is asserted. Any partition mismatch is an apparatus inconsistency and ends the diagnostic.

## Decision rule

- If any state-aligned rival passes T2: `DIAGNOSTIC_V153_STATE_ALIGNED_RIVAL_SOLVES_T2`.
- Else if all six seed-level rivals are transported and reach the native verifier with no R10: `DIAGNOSTIC_V153_STATE_ALIGNED_CANDIDATE_SET_SEMANTIC_TRAP`.
- Else if any native infrastructure error occurs: `R10_DIAGNOSTIC_INCONCLUSIVE`.
- Else if any state-aligned transport or grounding assertion fails: `R10_STATE_ALIGNMENT_INCONSISTENT`.

## Claim boundary

A solving frozen rival would show that V153's negative/obstructed outcome was caused by controller state semantics or rank/execution policy, not absence of a solving candidate in the frozen raw-T1 call-2 set. It would not by itself establish developmental dependence on T1 memory; that requires a paired control comparison under the corrected state semantics.

If every aligned rival fails, the result only establishes a semantic trap for the finite frozen V153 candidate set. It does not establish that the model cannot leave that basin under another search policy, budget, or representation.