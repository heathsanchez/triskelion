# V164 — Downstream Developmental Test on keras/32

## Purpose

V163 prospectively qualified the frozen semantic capability on the natural qualification case `thefuck/32`: `SEM_CONFIRM` solved 2/3, while opaque, cold, raw, and RAG controls solved 0/3. V164 is the already-licensed downstream test. It asks whether admitting that qualified capability into replayable developmental state changes native verified reachability on the already-frozen next natural case `keras/32`.

V164 is not allowed to alter the capability, scope, task, model, seeds, budget, routing policy, or controls after downstream outcomes are observed.

## Frozen lineage

- Acquisition evidence predates V159 and is frozen in `cp3_frozen/acquisition/CAPABILITY.json`.
- Natural downstream order was frozen in V159 before qualification outcomes.
- V159 selected `thefuck/32` as qualification and `keras/32` as downstream because they were the first two READY scope-matched cases in that frozen order.
- V163 qualified the semantic capability under a 3-call persistent verifier loop against opaque, cold, raw, and RAG controls.
- V164 may therefore admit that exact capability into `A_t`; no capability revision is permitted.

## Frozen apparatus

- Task: `keras/32` from BugsInPy commit `11c5f1eea954a42132cfd06bf257766a7963e0fd`.
- Model: `Qwen/Qwen3.5-9B` through the frozen River provider.
- Seeds: `202608171`, `202608172`, `202608173`.
- Maximum calls: 3 per seed/arm.
- Exact historical native verifier.
- Fresh independent checkout per seed/arm.
- Persistent workspace within each seed/arm across calls.
- Post-failure current-source synchronization before later calls.
- Structured-edit trust boundary unchanged.
- No hand-specified downstream locus and no binding packet. Routing on keras/32 must come from the ordinary task context plus the retained state/memory treatment of the arm.

## Developmental state

Before downstream inference, V164 must construct replayable `A_t` and admit the exact frozen capability using V163 as verified qualification evidence. It must serialize and replay the event stream and require:

1. event-chain validity;
2. identical state hash before/after restart;
3. capability active on the frozen keras/32 task context under its already-frozen scope.

Failure of any restart/scope invariant is apparatus obstruction, not a developmental negative.

## Frozen arms

1. `DEV_ADMITTED`: memory rendered from the admitted capability in replayed `A_t`.
2. `ANCESTOR_MINUS`: identical developmental apparatus with the qualified capability absent.
3. `OPAQUE_MATCHED`: same-length opaque rendering of the admitted capability manifest.
4. `RAW`: frozen raw acquisition memory.
5. `RAG`: deterministic retrieval from that same frozen raw memory for keras/32.

No arm receives V160's thefuck-specific locus signal.

## Primary endpoint

Native verified solve of keras/32 within three calls.

## Secondary endpoints

- executable call-1 edit;
- executable post-first verifier-guided refinement;
- transport failures;
- verifier calls;
- calls to solve;
- solved edit payload hashes.

Mechanism endpoints cannot substitute for the primary endpoint.

## Frozen interpretation gate

Let `S_dev` be `DEV_ADMITTED.solved_n`, and `S_alt_max` be the maximum solved count among `ANCESTOR_MINUS`, `OPAQUE_MATCHED`, `RAW`, and `RAG`.

- `PASS_V164_NATURAL_DEVELOPMENTAL_COMPOUNDING` iff all arms have 3 comparable seeds, restart/scope invariants pass, `S_dev >= 1`, and `S_dev > S_alt_max`.
- `V164_DOWNSTREAM_NOT_SEMANTICALLY_IDENTIFIED` iff all arms are comparable, `S_dev >= 1`, but one or more alternatives tie or beat `S_dev`.
- `NEGATIVE_V164_QUALIFIED_ANCESTOR_NO_DOWNSTREAM_ADVANTAGE` iff all arms are comparable and `S_dev == 0` or does not exceed alternatives.
- `OBSTRUCTED_V164_STATE_OR_SCOPE` iff replay/state/scope invariants fail.
- `OBSTRUCTED_V164_R10_INSUFFICIENT_COMPARABLE` iff any arm has fewer than 3 comparable seeds.

A PASS is bounded evidence of natural developmental compounding: an earlier externally qualified capability, admitted into replayable state and restarted, causally improves verified reachability on a later source-distinct natural task relative to ancestor-minus and matched memory controls. It is not a claim of general autonomous self-improvement.
