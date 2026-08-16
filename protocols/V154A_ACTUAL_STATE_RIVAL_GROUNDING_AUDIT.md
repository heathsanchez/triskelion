# V154A Actual-State Rival Grounding Audit — Frozen Protocol

## Purpose

V154 corrected the demonstrated V153 reset-state mismatch by keeping one T2 workspace across call 1, native-verifier failure, and call 2. Its frozen result was negative at the developmental comparison level: compiled O1 advantage NULL, raw T1 advantage NULL, and 0/3 solves in every arm. However, no deterministically selected call-2 rival reached the verifier in any arm.

V154A asks the smallest remaining apparatus/search question with zero new model calls and zero verifier calls:

**Did any of the three call-2 alternatives already emitted in V154 apply exactly to the actual source state that existed before call 2, even when the rank-1 selected alternative did not?**

This distinguishes rank-selection failure from state-grounding mismatch and from candidate-set transport failure.

## Frozen evidence

Source run: V154 persistent-workspace developmental separator, GitHub Actions run `31944944894`, commit `d13d1f0c5b22570a33da321cf995233514e3b0c1`, artifact `v154-persistent-workspace-developmental-separator` (artifact ID `9263077436`).

The source artifact was uploaded by the completed V154 workflow with artifact ZIP SHA256:

`485cfaf13fbd8b5227e20b66aedb66eed421753311dada89f837e5ea9b6f0b5f`

V154's frozen protocol SHA256 was:

`0feda5944d872e844b3f6c5ce436827c9ac874a8507b89eea429dfb8bc1b9725`

V154's frozen executable SHA256 was:

`41d90ad44c809cbdb2086df1a1ea3dfab3e150b2d30299c23c26e1e41f080689`

Task: BugsInPy `youtube-dl/32`.

Arms and seeds are inherited from V154:

- `D_COLD`
- `D_PLUS_O1_COMPILED`
- `D_PLUS_RAW_T1`
- `D_PLUS_SHAM_O1`
- `D_PLUS_SHAM_RAW`
- seeds `202608161`, `202608162`, `202608163`

## Actual pre-call-2 state

For each arm/seed, start from an independent exact buggy T2 checkout.

Inspect the frozen V154 call-1 record:

- If call 1 has a native `verdict`, its structured edit successfully applied before verification. Reapply that exact normalized call-1 edit to reconstruct the persistent post-call-1 state.
- If call 1 has no native `verdict`, its edit did not successfully apply. The actual pre-call-2 state is therefore the clean buggy checkout.

No inference from natural-language feedback is allowed; state is reconstructed solely from the recorded execution event.

## Candidate projection

Read the immutable raw call-2 response for each arm/seed and project all alternatives in the declared `{"alternatives":[...]}` schema. For every alternative with a syntactically valid `edits` list, normalize it through `structured_edit_protocol_v2.extract_edits`.

For each projected alternative record:

- rank 1/2/3
- payload SHA256
- duplicate-of-call1 status
- whether it applies exactly to ACTUAL pre-call-2 state
- whether it applies exactly to CLEAN buggy state
- first exact-transport failure on each state, including file, edit index, and `old` occurrence count
- whether it equals the V154 controller-selected payload

Exact application uses the same sequential invariant as the live structured-edit executor: each target file must exist and each `old` fragment must occur exactly once at the moment of replacement.

## Decision rule

Let a `missed executable rival` be an arm/seed where the V154 selected call-2 payload did not reach the verifier, but at least one other distinct non-call1 alternative applies exactly to ACTUAL state.

- If at least one missed executable rival exists: `DIAGNOSTIC_V154_SELECTION_POLICY_MISSES_EXECUTABLE_RIVAL`.
- Else, if at least one call-2 candidate fails ACTUAL but applies CLEAN while ACTUAL is post-call-1: `DIAGNOSTIC_V154_STATE_SEMANTICS_STILL_MIXED`.
- Else, if at least one valid projected alternative exists but none applies ACTUAL in any arm/seed: `DIAGNOSTIC_V154_CANDIDATE_SET_NOT_EXECUTABLE_ON_ACTUAL_STATE`.
- Else, if some alternatives apply ACTUAL but only the selected alternatives failed for reasons not reproduced by exact simulation: `R10_V154_EXECUTION_AUDIT_INCONSISTENT`.
- If immutable V154 evidence or exact T2 source cannot be reconstructed: `R10_DIAGNOSTIC_INCONCLUSIVE`.

## Claim boundary

This is an apparatus/search diagnostic, not a developmental-capability test. It cannot turn V154 into a positive developmental result. It determines which intervention is licensed next:

- selection-policy repair if executable non-selected rivals already exist;
- state-addressing repair if candidates systematically target CLEAN instead of the actual persistent state;
- source-grounding/search repair if the entire emitted set is non-executable on actual state.
