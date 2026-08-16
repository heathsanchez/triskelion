# V153F Exhaustive Rival Replay Diagnostic — Frozen Protocol

## Purpose

V153 established an obstruction at reliable rival generation under its frozen controller, while V153D showed that distinct concrete edit payloads can be recovered from the immutable V153 call-2 outputs and can reach the native verifier. V153E showed that at least one distinct rival can also execute on cumulative post-call-1 state. These results leave a narrower unresolved separator:

**Does the frozen V153 candidate set already contain a T2-solving rival that the deterministic rank-1 selection policy failed to choose, or are all generated rivals semantically trapped?**

This diagnostic answers only that question. It makes zero new model calls.

## Frozen evidence

Source artifact: V153 set-valued rival-search run `31943774314`, artifact `v153-set-valued-rival-search`.

Required `V153_RESULT.json` SHA256:

`ae572174c253b47cef2db706254b45675a8c414feeb8d6bf7c86d516bd206057`

Task: BugsInPy `youtube-dl/32` under the exact historical Python 3.7.4 image already frozen by V153.

Arm inspected: `D_PLUS_RAW_T1` only. This is the arm relevant to V153's raw developmental-memory separator.

Known falsified call-1 payload SHA256:

`69002ebf51a2842e41639dd21d1d5c196ee65feac42470bdbef24067264f40bb`

## Procedure

For each of the three frozen V153 seeds:

1. Read the immutable call-2 raw response.
2. Project every syntactically valid `edits` array using the same structured-edit normalizer used by V153D.
3. Deduplicate by normalized payload SHA256.
4. Exclude the known falsified call-1 payload.
5. For **every remaining distinct payload**, create a fresh buggy `youtube-dl/32` checkout, apply that payload alone, and run the exact native verifier.
6. Record transport failures, infrastructure failures, verifier failures, and verified solves separately.

No candidate is selected by rank. No new inference, repair, mutation, or semantic cherry-picking is allowed.

## Decision rule

- If any distinct frozen rival passes T2: `DIAGNOSTIC_V153_SELECTION_POLICY_OBSTRUCTION`. The candidate generator had already produced a solving action; the V153 deterministic first-distinct selector failed to exploit it.
- If at least two distinct rivals are executable and all executable rivals fail T2: `DIAGNOSTIC_V153_CANDIDATE_SET_SEMANTIC_TRAP`. Payload diversity exists, but the frozen candidate set contains no solving rival among those executable under the original clean-checkout semantics.
- If distinct rivals exist but fewer than two are executable: `DIAGNOSTIC_V153_EXECUTION_COVERAGE_INSUFFICIENT`.
- Any native infrastructure error: `R10_DIAGNOSTIC_INCONCLUSIVE`.

## Claim boundary

This is a zero-call diagnostic, not a developmental-capability test. A selection-policy verdict does not establish O1→O2 developmental dependence. A candidate-set semantic-trap verdict does not prove the model cannot generate a solving rival under another search policy or budget. It only localizes the frozen V153 residual.