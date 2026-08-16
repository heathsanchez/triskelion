# V154 — Projected, state-routed rival search

Frozen: 2026-08-16 NZST
Controller: Rigorous Breakthrough Stack v1.1

## Purpose

Run the first prospective T1→T2 causal separator in this lineage with all representation/execution defects isolated by V149–V153F removed without increasing the frozen model-call or semantic-verifier budget.

## Prior evidence boundary

- V149 repaired distorted visible-source context.
- V150 showed unified-diff transport was a real confounder but did not reveal a solution.
- V151B showed neither compiled O1 nor RAW T1 solved T2 under structured exact-replacement edits, but call 2 collapsed to the same candidate.
- V152 threaded the exact falsified action and still produced the same candidate.
- V153 changed only call 2 to a ranked three-rival set. Its strict envelope parser accepted RAW rivals on only 1/3 seeds, but post-hoc V153D byte projection found independently decodable `edits` payloads on 3/3 RAW seeds.
- V153F, after a pristine-cache gate, established that the first selected RAW rival was baseline-relative on one seed and call-1-state-relative on two seeds. All frozen rivals that reached the native verifier failed.

None of V153D/E/F changes V153's preregistered verdict or supplies semantic task knowledge to V154.

## Frozen substrate

Unchanged:

- T1 = `httpie/5`
- T2 = `youtube-dl/32`
- model = `Qwen/Qwen3.5-9B`
- seeds = `202608161`, `202608162`, `202608163`
- maximum two model calls per arm/seed
- maximum 2048 output tokens per call
- exact historical native verifier and precompiled checkout apparatus
- V149 exact-definition source context resolver
- exact V149 compiled O1 artifact SHA-256 `7ebb7fb26da6d137c13c1a08bafd7e540dbd52f25e04cf4298502e5ce5428546`
- exact T1 intervention SHA-256 `b7f419e7993e92164969b7a99689f01dfa279ce2d1615e25fce0bb21486f472d`
- five matched arms: `D_COLD`, `D_PLUS_O1_COMPILED`, `D_PLUS_RAW_T1`, `D_PLUS_SHAM_O1`, `D_PLUS_SHAM_RAW`
- identical memory/sham objects, task evidence, seed schedule, stopping rule, and causal reachability/efficiency classifier.

No T2 developer repair or protected test source is inspected or exposed.

## Call 1

Exactly the V151/V152/V153 structured-edit repair call. If a call-1 payload applies, it is verified once. If it fails, its exact normalized payload, SHA-256 and verifier failure tail become same-seed call-2 state.

## Call 2 proposal representation

Exactly one final model call requests a ranked set of three substantively different repair rivals, as in V153.

### Payload projection adapter

The controller does not require the surrounding diagnosis/envelope JSON to parse. It scans call-2 bytes left-to-right for the exact literal key token `"edits":`. At each occurrence it invokes the standard JSON decoder immediately after the colon and accepts the value only if:

1. it decodes as a JSON array; and
2. wrapping that unchanged value as `{ "edits": value }` validates through `structured_edit_protocol_v2.extract_edits`.

No path/old/new string is modified or repaired. Diagnosis text is ignored because it is not used for controller selection.

Payloads retain byte order. Exact duplicates are deduplicated by canonical payload SHA-256. The first valid payload whose SHA differs from call 1 is selected. No later payload may be chosen after transport or verifier failure.

## Deterministic source-state router

The selected call-2 payload is tested for **transport applicability only**, never semantic correctness, against two independently prepared states:

- `BASELINE`: pristine buggy T2 checkout;
- `CALL1_STATE`: the same pristine state after applying call 1's exact payload.

Applicability means the selected structured payload applies cleanly under the exact-replacement rules. Native tests are not run during routing.

Routing is frozen:

- baseline applies, call1-state does not → execute on `BASELINE`;
- call1-state applies, baseline does not → execute on `CALL1_STATE`;
- both apply → execute on `BASELINE`;
- neither applies → transport failure.

After route selection, create a fresh checkout, construct only the selected route state, apply the selected rival, and run the native verifier once. No fallback route or later rival is allowed after failure.

Thus call 2 still has one model call and at most one semantic verifier trial.

## Pristine template gate

Before arm execution, the normal T2 baseline preparation must establish a pristine failing checkout under the exact runtime. Candidate-modified work may never seed the reusable template. Any source-hash or infrastructure inconsistency is R10.

## Frozen gates

### G1 — Rival generation

RAW T1 is rival-generating on a seed iff projection yields at least one valid selected payload distinct from call 1.

`PASS_V154_RIVAL_GENERATION` requires >=2/3 RAW seeds.

### G2 — Rival semantic reachability

`PASS_V154_RIVAL_EXECUTION` requires >=1 RAW selected rival to route, apply, and reach the native verifier.

### G3 — Developmental advantage

Compiled O1 and RAW T1 retain V151's matched classifier:

- target must beat/tie controls under the preregistered reachability then efficiency rule;
- compiled O1 compares to cold + O1-length sham;
- RAW T1 compares to cold + RAW-length sham.

Classifications:

- `PASS_V154_COMPILED_DEVELOPMENTAL_SIGNAL`
- `PASS_V154_RAW_DEVELOPMENTAL_SIGNAL`
- `PASS_V154_CAPABILITY_COMPILATION_LOSS` iff RAW is non-null and compiled is null.

### G4 — Strong bounded negative

`NEGATIVE_V154_NO_T1_DEVELOPMENTAL_SIGNAL_UNDER_PROJECTED_STATE_ROUTED_RIVAL_SEARCH` only if:

- G1 passes;
- G2 passes;
- all five arms have all three comparable seeds and no R10;
- neither compiled O1 nor RAW T1 has a non-null advantage.

If G1 fails: `OBSTRUCTED_V154_NO_RIVAL_GENERATION`.
If G1 passes but G2 fails: `OBSTRUCTED_V154_RIVALS_DO_NOT_REACH_VERIFIER`.

## Claim boundary

A positive developmental classification remains bounded to this exact T1→T2 BugsInPy/Qwen substrate. A G4 negative is a materially stronger bounded negative than V151B/V152/V153 because visible context, patch transport, failed-action state, set-valued search, rival-envelope projection, and source-state execution have each been separately controlled. It does not imply no other model, budget, memory compiler, search operator, or task sequence could show developmental transfer.
