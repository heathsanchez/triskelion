# V154B Exact-Parser Actual-State Rival Audit — Frozen Protocol

## Purpose

V154A was inconclusive because its diagnostic parser required the entire call-2 response to parse without completion, while the live V154 controller used `structured_edit_protocol_v2._json_object`, which permits one strictly bounded syntactic operation: appending up to three unambiguous missing JSON container closers at EOF. No strings, keys, values, or existing punctuation are changed.

V154B repeats the frozen V154A scientific question using the **exact parser used by V154 itself**. No model calls and no verifier calls are permitted.

## Frozen evidence

Source V154 run: `31944944894`, commit `d13d1f0c5b22570a33da321cf995233514e3b0c1`, artifact `v154-persistent-workspace-developmental-separator`, artifact ID `9263077436`.

Required `V154_RESULT.json` SHA256, established by V154A before its audit:

`bb076d3f18d6eddd78b8093fb392280c012c9b69f526856bbb0e114abf8f2881`

V154A run `31945309654` is used only to establish that artifact hash and the parser-adapter residual; its scientific verdict was `R10_DIAGNOSTIC_INCONCLUSIVE` and is not used as evidence about rival grounding.

## Parser invariant

Call-2 responses must be parsed by `structured_edit_protocol_v2._json_object` from this repository. This is the same function imported by `v153_set_valued_rival_search.parse_ranked_rivals` and therefore by V154.

After object recovery:

1. Require `alternatives` to be a list.
2. Inspect at most the first three alternatives, preserving declared rank.
3. Normalize each `edits` list with `structured_edit_protocol_v2.extract_edits`.
4. Recompute the V154 deterministic selection rule: first valid payload distinct from call 1 and earlier rivals.
5. Assert that recomputed selected rank and payload SHA256 match V154's recorded `selected_rank` and `selected_payload_sha256`. Any mismatch is R10.

## Actual-state reconstruction

For every arm/seed, begin from an independent exact buggy `youtube-dl/32` checkout.

- If frozen call 1 contains a native verifier record, reapply its normalized edit: ACTUAL state is POST_CALL1.
- Otherwise ACTUAL is CLEAN.

Simulate each valid call-2 alternative independently on CLEAN and ACTUAL using exact sequential structured-edit transport semantics.

## Decision rule

Let a missed executable rival be an arm/seed where V154's selected rival did not reach the verifier, but a non-selected, non-call1 valid alternative applies exactly to ACTUAL state.

- Any parser-selection mismatch with frozen V154: `R10_V154_PARSER_REPLAY_MISMATCH`.
- Else if any missed executable rival exists: `DIAGNOSTIC_V154_SELECTION_POLICY_MISSES_EXECUTABLE_RIVAL`.
- Else if any candidate fails ACTUAL but applies CLEAN while ACTUAL is POST_CALL1: `DIAGNOSTIC_V154_STATE_SEMANTICS_STILL_MIXED`.
- Else if valid alternatives exist and none applies ACTUAL: `DIAGNOSTIC_V154_CANDIDATE_SET_NOT_EXECUTABLE_ON_ACTUAL_STATE`.
- Else if ACTUAL-executable candidates exist without a selection miss: `DIAGNOSTIC_V154_EXECUTABLE_RIVALS_EXIST_BUT_NO_SELECTION_MISS`.
- Otherwise: `R10_DIAGNOSTIC_INCONCLUSIVE`.

## Claim boundary

This remains an apparatus/search diagnostic. It cannot create developmental evidence. It identifies the smallest licensed intervention after V154 by faithfully replaying the exact structured-output semantics under which V154 ran.
