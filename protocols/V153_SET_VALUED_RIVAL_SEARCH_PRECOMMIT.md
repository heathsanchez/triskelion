# V153 — Set-valued rival-search separator

Frozen: 2026-08-16 NZST
Controller: Rigorous Breakthrough Stack v1.1

## Residual

V152 threaded the exact verifier-disproved call-1 edit, its SHA-256, and native verifier failure into call 2 for every matched arm. The controller explicitly instructed the model not to repeat the same or an equivalent mechanism. Nevertheless, across all five arms and all three frozen seeds, call 2 emitted the exact same normalized edit as call 1. In the RAW T1 arm, distinct second candidates remained 0/3 and no second candidate reached the verifier. The V152 verdict was `OBSTRUCTED_SEARCH_POLICY_STILL_COLLAPSED`.

This establishes an absorbing single-proposal attractor under the frozen single-best repair interface. It does not establish that the model cannot represent or generate rival repair hypotheses.

## Question

If the second and final model call must emit a ranked set of rival repair hypotheses in one response, can the controller escape the verifier-disproved attractor without increasing model-call or native-verifier budgets, and does T1 memory then causally improve T2 acquisition?

## Frozen substrate

Unchanged from V152:

- T1 = `httpie/5`
- T2 = `youtube-dl/32`
- model = `Qwen/Qwen3.5-9B`
- frozen seeds = `202608161`, `202608162`, `202608163`
- maximum two model calls per arm/seed
- maximum 2048 output tokens per call
- exact historical BugsInPy native verifier and precompiled checkout apparatus
- V149 exact-definition context resolver
- structured exact-replacement production edits only
- exact V149 O1 artifact SHA-256 `7ebb7fb26da6d137c13c1a08bafd7e540dbd52f25e04cf4298502e5ce5428546`
- exact T1 verified intervention SHA-256 `b7f419e7993e92164969b7a99689f01dfa279ce2d1615e25fce0bb21486f472d`
- five arms: `D_COLD`, `D_PLUS_O1_COMPILED`, `D_PLUS_RAW_T1`, `D_PLUS_SHAM_O1`, `D_PLUS_SHAM_RAW`
- identical retained-memory objects and sham-length matching
- same first-call prompt and first-call controller behavior as V152
- same comparison/classification rules for compiled O1 and RAW T1

No developer repair for T2 is inspected or exposed.

## Single intervention

Only the **representation of call-2 proposal search** changes.

After a call-1 candidate is executed and fails the native verifier, call 2 receives the same state as V152:

1. unchanged original buggy evidence;
2. unchanged arm memory, if any;
3. exact normalized call-1 edit payload and SHA-256;
4. native verifier failure tail;
5. explicit statement that the executed hypothesis is falsified.

Instead of requesting one replacement edit, call 2 must return exactly one JSON object with key `alternatives`, whose value is a ranked list of exactly three objects. Each object has:

- `diagnosis`: short natural-language mechanism description;
- `edits`: 1–3 structured exact-replacement edits using the same production-source constraints as V151/V152.

The three alternatives must represent substantively different repair mechanisms from the falsified call-1 candidate and from one another.

This is one model call, not three calls.

## Deterministic controller selection

The controller parses alternatives in emitted order and canonicalizes each `edits` list through the existing structured-edit validator.

For each alternative it records:

- emitted rank;
- parse/validation status;
- canonical payload SHA-256;
- whether it duplicates the falsified call-1 payload;
- whether it duplicates an earlier call-2 alternative.

The controller selects the **first valid, exact-hash-distinct call-2 alternative in emitted order**. It does not inspect verifier outcomes to select among alternatives.

Only that selected alternative is applied and sent to the native verifier. Thus call 2 still contributes at most one native-verifier trial. No third model call is allowed.

If all alternatives are malformed or exact duplicates, call 2 fails as `NO_DISTINCT_VALID_RIVAL` and no verifier call is made.

If the selected distinct alternative fails transport after canonical validation/application, the arm/seed is unsolved; no fallback to a later alternative is permitted. This avoids outcome-guided selection.

## Frozen gates

### R1 — Rival generation breaks the absorbing attractor

For the RAW T1 arm, define a seed as rival-generating iff call 2 contains at least one valid normalized alternative whose SHA-256 differs from the verifier-disproved call-1 payload.

`PASS_V153_RIVAL_GENERATION` iff:

- at least 2/3 RAW seeds are rival-generating; and
- this is strictly above V152 RAW's frozen 0/3 distinct-second-candidate baseline.

This is a search/apparatus result only.

### R2 — Rival execution reaches semantics

`PASS_V153_RIVAL_EXECUTION` iff at least one RAW seed selects a distinct call-2 rival that applies successfully and reaches the native verifier.

### R3 — Developmental advantage

Compiled O1 and RAW T1 use the unchanged V151 reachability/efficiency comparison against `D_COLD` plus their matched sham controls.

- `PASS_V153_COMPILED_DEVELOPMENTAL_SIGNAL` iff compiled O1 has non-null causal advantage.
- `PASS_V153_RAW_DEVELOPMENTAL_SIGNAL` iff RAW T1 has non-null causal advantage.
- `PASS_V153_CAPABILITY_COMPILATION_LOSS` iff RAW T1 has non-null advantage while compiled O1 does not.

### R4 — Stronger bounded negative

`NEGATIVE_V153_NO_T1_DEVELOPMENTAL_SIGNAL_UNDER_RIVAL_SEARCH` only if:

- R1 passes;
- R2 passes;
- all matched comparisons are free of R10;
- neither compiled O1 nor RAW T1 has a non-null advantage.

If R1 fails, classify `OBSTRUCTED_V153_NO_RIVAL_HYPOTHESIS_GENERATION`.
If R1 passes but R2 fails, classify `OBSTRUCTED_V153_RIVALS_DO_NOT_REACH_VERIFIER`.

## Claim boundary

A rival-generation pass means the same model can generate alternatives when proposal representation is set-valued, despite collapse under single-best decoding. It does not establish that any rival is correct. A developmental pass remains bounded to this frozen T1→T2 BugsInPy/Qwen substrate. A negative applies only under the two-call controller with one ranked three-rival proposal set and one selected semantic trial on call 2. No result establishes unrestricted recursive improvement or a three-rung developmental chain.
