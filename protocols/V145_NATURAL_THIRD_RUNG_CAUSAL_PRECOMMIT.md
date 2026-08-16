# V145 — Natural third-rung causal frontier precommit

Frozen: 2026-08-16 NZST
Controller: Rigorous Breakthrough Stack v1.1

## Question

Does retaining a verified capability from a first natural BugsInPy episode causally improve acquisition of a second capability, and does retaining both causally improve a third source-distinct natural episode under matched budgets?

This experiment is downstream of V141 only. V141 established that `pandas/66` is a naturally qualified third acquisition episode under the frozen 501-bug corpus order. It did not establish O3 or development.

## Frozen natural stream

The task order is frozen before this experiment inspects any new model outcomes:

1. T1 = `httpie/5`
2. T2 = `youtube-dl/32`
3. T3 = `pandas/66`

T1 and T2 were already frozen acquisition cases in `cp3/KNOWN_QUALIFIED.json`. T3 is the first V141-qualified pandas case under SHA256(project/id) lexical order. Projects are source-distinct.

No task may be substituted after model outcomes are observed.

## Verifier and environment

Use the existing BugsInPy native verifier with pinned exact historical CPython Docker images from `cp3/bugsinpy_exact_runtime.py`. A task is semantically solved only when its native verifier passes after the model patch. Checkout/provision/network/provider/compile apparatus failures are R10 and have no semantic meaning.

## Base model and budget

- Model: `Qwen/Qwen3.5-9B`
- Provider serialization: existing `Qwen35ChatRiverProvider`, thinking disabled.
- Seeds: `202608161`, `202608162`, `202608163` for every compared arm.
- Maximum two model repair calls per seed/arm.
- Maximum model output: 2048 tokens per call.
- After a failed first candidate, call 2 may see only the same visible buggy evidence plus verifier feedback from call 1 in that same arm/seed.
- Each attempt starts from a disposable fresh buggy checkout; no protected developer patch is visible to the repair model.

## Capability construction

### O1

O1 is synthesized **before any T2 model outcome is observed** from the verified T1 acquisition intervention trace only. The T1 developer patch is allowed acquisition evidence, as in the pre-existing CP3 acquisition boundary; it is never shown as protected T2/T3 evidence. The synthesis model must produce a portable policy and may not name the source project/case.

### O2

O2 may be synthesized only after an O1-arm T2 repair is independently verified. O2 is an incremental portable policy synthesized from that verified T2 intervention plus the already-frozen O1 manifest. It may not name T1/T2/T3 project identities and may not include T3 evidence.

O2 is retained as a separate object from O1. The ancestor-ablation arm supplies O2 without O1.

### O3

A verified T3 repair in the developmental arm may be frozen afterward as O3, but this is not sufficient for a developmental PASS. The causal arm gates below decide whether the third rung was enabled by retained ancestors.

## T2 matched causal arms

For each frozen seed:

- `D_COLD`: no retained capability.
- `D_PLUS_O1`: O1 manifest appended to the same visible task evidence.
- `D_PLUS_SHAM`: deterministic capability-shaped filler matched to O1 serialized character length, containing no repair semantics.

Task, source context, verifier, seed, max calls, max tokens and stopping rule are identical.

T2 causal advantage is classified as:

- `REACHABILITY`: O1 solves strictly more frozen seeds than both cold and sham.
- `EFFICIENCY`: solve counts tie the best control, but O1 has strictly lower median calls-to-verified-solution among jointly solved seeds; if call medians tie, strictly lower median generated token count may decide.
- otherwise `NULL_T2_NO_CAUSAL_ADVANTAGE`.

O2 can be constructed whenever at least one O1-arm T2 repair is verified, but the strong developmental chain requires a non-null T2 causal advantage.

## T3 matched causal arms

Only if O2 can be constructed, run for every frozen seed:

- `D_COLD`
- `D_PLUS_O1`
- `D_PLUS_O1_O2`
- `D_PLUS_O2_ANCESTOR_ABLATED`
- `D_PLUS_SHAM`, with deterministic filler matched to the serialized length of O1+O2.

The same task evidence, verifier, seed schedule, two-call budget, token budget and stopping rule are held fixed.

T3 advantage is `REACHABILITY` only if `D_PLUS_O1_O2` solves strictly more seeds than cold, O1-only, O2-only ancestor ablation and sham. It is `EFFICIENCY` if reachability ties but the developmental arm strictly improves the preregistered calls/tokens criterion against all relevant tied controls.

## Strong causal third-rung PASS

`PASS_V145_CAUSAL_THREE_RUNG_DEVELOPMENT` requires all of:

1. T1 intervention independently verifies and O1 is frozen before T2 outcomes.
2. T2 has a non-null O1 causal advantage under the matched arms.
3. At least one O1-assisted T2 repair verifies and O2 is frozen before T3 outcomes.
4. T3 `D_PLUS_O1_O2` has a non-null causal advantage over cold and O1-only.
5. Ancestor ablation (`O2` without `O1`) is strictly worse on reachability or the preregistered cost criterion.
6. Sham does not reproduce the developmental advantage.
7. All three tasks remain source-distinct and all semantic successes are native-verifier successes.
8. No R10 event is counted as a semantic failure for a causal comparison; if an arm/seed is R10, its matched seed is excluded from that comparison and reported.

If T2 or T3 gains are cost-only, the verdict must say `FRONTIER_EFFICIENCY`, not new reachability.

## Costs recorded

Per arm/seed:
- model calls made;
- generated token count where provider metadata exposes it, otherwise exact output character count as an explicitly labelled proxy;
- native verifier calls;
- verifier wall-clock milliseconds;
- total wall-clock milliseconds;
- retained-state serialized bytes/chars;
- patch parse/apply failures;
- R10 events.

## Claim boundary

A PASS would establish a bounded three-episode, source-distinct causal developmental chain for this frozen BugsInPy/Qwen repair substrate. It would not establish unrestricted recursive self-improvement or open-ended development. A null/negative is first-class evidence. Infrastructure negatives carry no semantic conclusion.