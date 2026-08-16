# V152 — Attempt-state threading separator

Frozen: 2026-08-16 NZST
Controller: Rigorous Breakthrough Stack v1.1

## Residual

V151B produced a valid bounded negative on `youtube-dl/32`: cold, compiled O1, raw verified T1 acquisition trace, and both length-matched sham controls all solved 0/3 frozen seeds within two calls. However, reduction of the immutable V151B artifact showed that the second repair call was stateless with respect to the first proposed edit: the prompt contained verifier feedback but did not contain the normalized first candidate itself. Across the RAW arm, all three seeds repeated the same verifier-disproved semantic edit on call 2.

Therefore V151B does not distinguish absence of developmental signal from a controller defect in which verifier-disproved action state is not threaded into the next search step.

## Question

When the exact prior normalized candidate is threaded into call 2, does the agent move to a distinct hypothesis, and does compiled O1 or raw T1 memory then causally improve acquisition of T2 relative to matched controls?

## Frozen substrate

Unchanged from V151B:

- T1 = `httpie/5`
- T2 = `youtube-dl/32`
- model = `Qwen/Qwen3.5-9B`
- seeds = `202608161`, `202608162`, `202608163`
- maximum two repair calls per seed/arm
- maximum output = 2048 tokens per call
- exact historical native verifier and precompiled checkout apparatus
- V149 exact-definition context resolver
- structured exact-replacement edit protocol v2
- exact V149 O1 artifact SHA-256 `7ebb7fb26da6d137c13c1a08bafd7e540dbd52f25e04cf4298502e5ce5428546`
- exact T1 verified intervention SHA-256 `b7f419e7993e92164969b7a99689f01dfa279ce2d1615e25fce0bb21486f472d`
- same five arms: `D_COLD`, `D_PLUS_O1_COMPILED`, `D_PLUS_RAW_T1`, `D_PLUS_SHAM_O1`, `D_PLUS_SHAM_RAW`
- same sham construction and retained-state sizes
- same classification comparison against the matching cold/sham controls

No developer patch or protected T2 repair is inspected or exposed.

## Single intervention

Only the call-2 controller state changes.

After a call-1 candidate successfully applies but fails the native verifier, call 2 receives:

1. the unchanged original visible buggy evidence;
2. the unchanged arm memory, if any;
3. the normalized structured-edit payload actually executed on call 1;
4. that payload's SHA-256;
5. the native verifier failure tail from call 1;
6. an instruction that the executed candidate is verifier-disproved and must not be repeated exactly or by an equivalent edit; call 2 must search a substantively different repair hypothesis.

The first candidate is model-produced evidence already generated inside the same arm/seed. Threading it adds no protected task information.

If call 1 fails transport before execution, call 2 receives the model's raw prior response plus the transport error, again solely to prevent blind regeneration of the same malformed action.

## Frozen novelty audit

For every arm/seed, record normalized edit-payload hashes for executed candidates.

- `distinct_second_candidate = true` iff call 2 yields a normalized payload hash different from the executed call-1 payload hash.
- An exact repeated payload is not sent to the native verifier a second time; it is recorded as `REPEAT_REJECTED` and remains a failed attempt under the fixed two-call budget.
- A different payload is verified normally.

This rejection changes no model-call budget and gives no arm an additional attempt.

## Outcomes

### S1 — Attempt-state threading works

`PASS_V152_STATE_THREADING_BREAKS_REPEAT_ATTRACTOR` iff at least 2/3 RAW seeds produce a distinct second candidate after a verifier-disproved call-1 candidate, and the rate is strictly above V151B RAW (0/3 distinct second candidates).

This is an apparatus/search result only, not developmental evidence.

### S2 — Developmental advantage under stateful search

Compiled O1 and RAW T1 advantages are classified with the same reachability/efficiency rule used in V151, each against `D_COLD` and its matched sham.

- `PASS_V152_COMPILED_DEVELOPMENTAL_SIGNAL` iff compiled O1 has non-null causal advantage.
- `PASS_V152_RAW_DEVELOPMENTAL_SIGNAL` iff raw T1 has non-null causal advantage.
- `PASS_V152_CAPABILITY_COMPILATION_LOSS` iff RAW has non-null advantage and compiled O1 does not.

### S3 — Stronger bounded negative

`NEGATIVE_V152_NO_T1_DEVELOPMENTAL_SIGNAL_UNDER_STATEFUL_SEARCH` only if:

- state threading passes S1;
- no R10 invalidates matched comparisons;
- neither compiled O1 nor RAW T1 has a non-null advantage;
- at least one distinct, successfully applied call-2 candidate reaches the native verifier in the RAW arm.

If S1 fails, the verdict is `OBSTRUCTED_SEARCH_POLICY_STILL_COLLAPSED`, not a developmental negative.

## Claim boundary

A developmental PASS is bounded to this frozen BugsInPy/Qwen/T1→T2 substrate. A state-threading PASS establishes only that preserving the agent's own verifier-disproved action state changes subsequent search. A negative applies only under this stateful two-call controller. No result licenses unrestricted recursive improvement or a three-rung claim.
