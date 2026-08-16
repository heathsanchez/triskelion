# V153G Rival Grounding-Origin Diagnostic — Frozen Protocol

## Purpose

V153F found six distinct frozen raw-T1 rivals, but only one was executable on the clean buggy T2 checkout. Five failed the structured-edit transport invariant because their `old` source text was absent. V153E separately established that at least one rival can execute on the cumulative post-call-1 state.

This zero-model-call diagnostic asks the next smallest question:

**Are the non-clean-grounded V153 rivals actually grounded in the post-call-1 source state, or are they ungrounded in either state?**

This distinguishes a controller/model state-semantics mismatch from genuine source-grounding failure.

## Frozen evidence

Source artifact: V153 set-valued rival-search run `31943774314`, artifact `v153-set-valued-rival-search`.

Required `V153_RESULT.json` SHA256:

`ae572174c253b47cef2db706254b45675a8c414feeb8d6bf7c86d516bd206057`

Task: BugsInPy `youtube-dl/32`.

Arm inspected: `D_PLUS_RAW_T1`.

Known call-1 normalized payload SHA256:

`69002ebf51a2842e41639dd21d1d5c196ee65feac42470bdbef24067264f40bb`

## State definitions

- `CLEAN`: exact buggy `youtube-dl/32` checkout before any model edit.
- `POST_CALL1`: CLEAN after applying the frozen call-1 structured edit exactly once using the same sequential replacement semantics as `structured_edit_protocol.apply_edits`.

No verifier, model, ranking, repair, rebasing, fuzzy matching, or semantic correction is permitted.

## Procedure

1. Recover the immutable V153 artifact and verify its hash.
2. Recover call 1 from each raw-T1 seed and verify that its normalized edit payload has the frozen SHA256 above.
3. Check out one exact buggy T2 source tree.
4. Snapshot all source files referenced by call 1 or any projected call-2 rival.
5. Construct CLEAN and POST_CALL1 states in memory using exact sequential `old`→`new` replacements.
6. Project every call-2 `edits` array exactly as in V153D/V153F, deduplicate normalized payloads per seed, and exclude the known call-1 payload.
7. For each distinct rival, simulate the complete payload independently on CLEAN and POST_CALL1 using the exact transport invariant: target file exists and each edit's `old` text occurs exactly once at the moment that edit is applied.
8. Record the first failing edit and occurrence count for each state.

## Classification

Each rival receives exactly one grounding class:

- `GROUND_BOTH`: applies to CLEAN and POST_CALL1.
- `GROUND_CLEAN_ONLY`: applies to CLEAN but not POST_CALL1.
- `GROUND_POST_CALL1_ONLY`: applies to POST_CALL1 but not CLEAN.
- `UNGROUNDED_BOTH`: applies to neither state.

## Decision rule

- If at least half of the non-clean-grounded distinct rivals are `GROUND_POST_CALL1_ONLY`: `DIAGNOSTIC_V153_STATE_SEMANTICS_MISMATCH`.
- Else if at least one rival is `GROUND_POST_CALL1_ONLY`: `DIAGNOSTIC_V153_MIXED_STATE_GROUNDING`.
- Else if any non-clean-grounded rivals remain and none ground post-call-1: `DIAGNOSTIC_V153_SOURCE_GROUNDING_FAILURE`.
- If call-1 provenance or CLEAN checkout cannot be established: `R10_DIAGNOSTIC_INCONCLUSIVE`.

## Claim boundary

This diagnostic does not establish developmental transfer, search competence, or repair capability. It only localizes why the frozen V153 rivals failed exact execution coverage. A state-semantics mismatch would license a later causal controller separator; a source-grounding failure would instead license an exact-source addressing intervention.